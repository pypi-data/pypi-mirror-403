import copy
import re

import numpy as np

import unac.util.data as d

# Table Layout
# Header values
MSMS_HEADERS = {
    "A1": "Measurement ID",
    # B1: reserved
    "C1": "Precursor",
    "D1": "Precursor backbone C-atoms",
    "E1": "Precursor m/z",
    "F1": "Precursor mass shift",
    "G1": "Product",
    "H1": "Product backbone C-atoms",
    "I1": "Product m/z",
    "J1": "Product mass shift",
    "K1": "Rep ID",
}

# column spec (define variables corresponding to column numbers of the headers)
MSMS_MID = 0  # aka A
MSMS_PRECURSOR = 2  # aka C (B is the new free text field)
MSMS_PRECURSOR_C = 3  # aka D
MSMS_PRECURSOR_MASS = 4  # aka E
MSMS_PRECURSOR_SHIFT = 5  # aka F
MSMS_PRODUCT = 6  # aka G
MSMS_PRODUCT_C = 7  # aka H
MSMS_PRODUCT_MASS = 8  # aka I
MSMS_PRODUCT_SHIFT = 9  # aka J
MSMS_REPLICATE = 10  # aka K
MSMS_FIRST_VAL = 11  # aka L


def verify_msms_structure(ws):
    """
    Verify that a given worksheet meets the specification
    :param ws:      the worksheet to investigate
    :return:        True if the worksheets meets the specification
    :rtype:         bool
    """
    # for every key (column title) in the MSMS_HEADERS dictionary
    for cell in MSMS_HEADERS:
        if (
            # isinstance: is object (first argument) an instance or subclass of second argument?
            # Here: is cell a string?
            not isinstance(ws[cell].value, str)
            # change any whitespace (space, tab, newline, ...) to ' ' (space) and convert to lower case before comparing
            or re.sub(r"\s+", " ", ws[cell].value.lower()) != MSMS_HEADERS[cell].lower()
        ):
            raise d.DataError(
                f"Value in cell {cell} was '{ws[cell].value}' but expected '{MSMS_HEADERS[cell].lower()}'.\nPlease "
                f"change your Excel input file accordingly."
            )
            return False
    return True


def build_mgroup_name(m_id, pre, pro):
    """
    Build a name that uniquely characterizes a measurement group
    Parameters
    ----------
    m_id:           measurement ID
    pre:            chemical formula for precursor
    pro:            chemical formula for product

    Returns
    -------
    a string with the name
    """
    # MS measurement
    if pre == pro:
        return f"{m_id}_{pre}"
    # MSMS measurement
    else:
        return f"{m_id}_{pre}_{pro}"


def import_raw_data(wb, sheet_name):
    """
    Parameters
    ----------
    wb:             An Excel workbook imported via openpyxl (wb = openpyxl.load_workbook(path)).
    sheet_name:     The name of sheet therein.

    Returns
    -------
    has_data:       True if MS or MSMS measurement data was found in the spreadsheet.
    collected_mids: A handy map with all the data from the spreadsheet as d.Measurement.
    """
    # wb is an openpyxl workbook, ws an openpyxl worksheet
    ws = wb[sheet_name]

    num_cols = ws.max_column

    val_columns = []
    times = []
    val_rows = []
    masses = []

    # was there any data at all?
    has_data = False
    collected_m_ids = {}

    active_measurement = None
    # check correct structure of worksheet
    if verify_msms_structure(ws):
        # locate all columns which contain measurement data -> collect in val_columns
        # range(12 (M) to all columns+1)
        for col_idx in range(MSMS_FIRST_VAL + 1, num_cols + 1):
            if ws.cell(column=col_idx, row=1).value is None:
                break
            elif "val" in ws.cell(column=col_idx, row=1).value.lower():
                raw_time = ws.cell(column=col_idx, row=1).value.lower()
                # delete 'val' and '@' to get only the time value
                time = raw_time.replace("val", "").replace("@", "").strip()
                val_columns.append(col_idx - 1)
                try:
                    time_f = float(time)
                except ValueError:
                    try:
                        time_f = float(time.replace(",", "."))
                    except ValueError:
                        headers = [header.value for header in ws[1]]
                        raise d.DataError(
                            f"Time-point {time} could not be converted to a number. Check if the header of column "
                            f'"{headers[col_idx - 1]}" is correctly phrased.\nThe correct phrasing for e.g. the '
                            f"value column containing data from time-point 25 s would be: 'Val @ 25' (omitting the "
                            f"quotation marks)"
                        )
                times.append(time_f)
            else:
                break

        # transform data to a nice numpy array
        # drop first row (header)
        spreadsheet_data = np.delete(np.array([[i.value for i in j] for j in ws.rows]), 0, 0)
        # make a fake row that differs from the last one. this way after the last real row it is easier to detect that
        # the file is over
        fake_row = copy.copy(spreadsheet_data[-1, :])
        fake_row[MSMS_MID] = f"not_{fake_row[MSMS_MID]}"
        fake_row[MSMS_PRECURSOR_C] = 0
        spreadsheet_data = np.vstack([spreadsheet_data, fake_row])
        # parse through the sheet row by row
        row_idx: int = 0
        next_msms: bool = True
        next_m_id: str = ""
        m_id: str = next_m_id
        next_pre: str = ""
        pre: str = next_pre
        next_pre_c: int = 0
        pre_c: int = next_pre_c
        next_pre_mass: float = 0
        pre_mass: float = next_pre_mass
        next_pro: str = ""
        pro: str = next_pro
        next_pro_c: int = 0
        pro_c: int = next_pro_c
        next_pro_mass: float = 0
        pro_mass: float = next_pro_mass
        next_rep: str = ""
        rep: str = next_rep
        for row in spreadsheet_data:
            # get all necessary information from a row and
            # a row with a possibly new MID
            if row[MSMS_MID] is not None:
                # .strip() removes leading and trailing whitespaces
                # str(None) does not lead to an error, int(None) and float(None) do
                next_m_id = str(row[MSMS_MID]).strip()
                try:
                    next_pre_c = int(row[MSMS_PRECURSOR_C])
                except (TypeError, ValueError):
                    print(row)
                    print(len(row))
                    # The first row of spreadsheet_data corresponds to row 2 of the original Excel sheet since Excel
                    # starts counting at 1 (as opposed to 0)  and the header was deleted -> therefore, the row in the
                    # Excel file is row_idx+2
                    raise d.DataError(
                        f"The cell {chr(ord('@')+MSMS_PRECURSOR_C+1)}{row_idx+2} (Column "
                        f"{MSMS_HEADERS[MSMS_PRECURSOR_C]}) contains an invalid entry ({row[MSMS_PRECURSOR_C]}). A "
                        f"whole number is expected."
                    )
                next_pre = str(row[MSMS_PRECURSOR]).strip()
                try:
                    next_pre_shift = int(row[MSMS_PRECURSOR_SHIFT])
                except TypeError:
                    raise d.DataError(
                        f"The 'Precursor Mass Shift' column contains a None Type in row {row_idx+2} (in cell "
                        f"F{row_idx+2}, to be exact) of your Excel input file."
                    )
                except (TypeError, ValueError):
                    raise d.DataError(
                        f"The cell {chr(ord('@')+MSMS_PRECURSOR_SHIFT+1)}{row_idx+2} (Column "
                        f"{MSMS_HEADERS[MSMS_PRECURSOR_SHIFT]}) contains an invalid entry ({row[MSMS_PRECURSOR_C]}). "
                        f"A whole number is expected."
                    )
                try:
                    next_pre_mass = float(row[MSMS_PRECURSOR_MASS])
                except TypeError:
                    next_pre_mass = np.nan
                # if the "Product" column in the Excel sheet contained nothing, then it is no tandem MS measurement
                # -> next_msms = False
                next_msms = row[MSMS_PRODUCT] is not None and row[MSMS_PRODUCT] != ""
                next_rep = str(row[MSMS_REPLICATE]).strip()
                # Using .strip() on (what was originally) a None type will work since it was converted to a string.
                # Therefore, use if instead of try/except for error detection.
                if next_rep == "None":
                    raise d.DataError(
                        f"The 'Rep ID' column contains a None Type in row {row_idx+2} (in cell K{row_idx+2}, to be "
                        f"exact) of your Excel input file.\nLeaving fields in this column empty will cause errors down "
                        f"the line so please add replicate IDs."
                    )
                # if this is a msms notation read in further data
                if next_msms:
                    try:
                        next_pro_c = int(row[MSMS_PRODUCT_C])
                    except ValueError:
                        raise d.DataError(
                            f"The Precursor Shift column in row {row_idx+2} does not contain an integer: "
                            f'"{row[MSMS_PRECURSOR_SHIFT]}"'
                        )
                    next_pro = str(row[MSMS_PRODUCT]).strip()
                    try:
                        next_pro_shift = int(row[MSMS_PRODUCT_SHIFT])
                    except ValueError:
                        raise d.DataError(
                            f"The Product Shift column in row {row_idx+2} does not contain an integer: "
                            f'"{row[MSMS_PRODUCT_SHIFT]}"'
                        )
                    # After getting the next product ion mass shift, make sure it is not higher than the precursor mass
                    # shift or lower than zero since both cases are not sensible.
                    if next_pro_shift > next_pre_shift:
                        raise d.DataError(
                            f"The product ion mass shift ({next_pro_shift}) in row {row_idx+2} is larger than its "
                            f"pertaining precursor ion mass shift ({next_pre_shift})."
                        )
                    elif next_pro_shift < 0:
                        raise d.DataError(
                            f"The value of the product ion mass shift ({next_pro_shift}) in row {row_idx+2} is less "
                            f"than 0."
                        )

                    try:
                        next_pro_mass = float(row[MSMS_PRODUCT_MASS])
                    except TypeError:
                        next_pro_mass = np.nan
                    if next_pre == next_pro:
                        next_msms = False
                # if it is ms, just copy everything from precursor to product
                else:
                    next_pro_c = next_pre_c
                    next_pro = next_pre
                    next_pro_shift = next_pre_shift
                    next_pro_mass = next_pre_mass
            # no new MID, so we just need to parse the mass shifts
            else:
                try:
                    next_pre_shift = int(row[MSMS_PRECURSOR_SHIFT])
                    if next_msms:
                        next_pro_shift = int(row[MSMS_PRODUCT_SHIFT])
                    else:
                        next_pro_shift = next_pre_shift
                except TypeError:
                    if next_msms:
                        raise d.DataError(
                            f"In row {row_idx + 2} of your Excel input file, the Precursor Mass Shift "
                            f"({row[MSMS_PRECURSOR_SHIFT]}) or Product Mass Shift ({row[MSMS_PRODUCT_SHIFT]}) could "
                            f"not be converted to an integer.\nPlease check the content of the corresponding cells."
                        )
                    else:
                        raise d.DataError(
                            f"In row {row_idx + 2} of your Excel input file, the (Precursor) Mass Shift "
                            f"({row[MSMS_PRECURSOR_SHIFT]}) could not be converted to an integer.\nPlease check the "
                            f"content of the corresponding cell."
                        )

            # if this is still the old measurement, add the values and the corresponding shifts
            if active_measurement == build_mgroup_name(next_m_id, next_pre, next_pro) and rep == next_rep:
                # this is data for the same measurement, i.e. a new mass lane
                val_rows.append(row_idx)
                masses.append(d.MassLane(next_pre_shift, next_pro_shift, next_msms))
                has_data = True
            else:
                # new measurement -> store data
                # read in the correct data
                if has_data:
                    met_data = spreadsheet_data[np.ix_(val_rows, val_columns)]
                    # the first time we see this measurement -> create entry
                    if active_measurement not in collected_m_ids:
                        try:
                            collected_m_ids[active_measurement] = d.Measurement(
                                m_id, masses, pre, pre_c, pre_mass, pro, pro_c, pro_mass
                            )
                        except d.DataError as err:
                            first_row = min(val_rows) + 2
                            raise d.DataError(f"Error in measurement {m_id} starting at row {first_row}: {err.msg}")
                    # add the data
                    try:
                        collected_m_ids[active_measurement].add_data(rep, times, met_data, masses)
                    except d.DataError as err:
                        first_row = min(val_rows) + 2
                        raise d.DataError(f"Error starting in line {first_row}: {err.msg}")

                # current row is the first row of a new measurement
                val_rows = [row_idx]
                m_id = next_m_id
                pre = next_pre
                pre_c = next_pre_c
                pre_mass = next_pre_mass
                pro = next_pro
                pro_c = next_pro_c
                pro_mass = next_pro_mass
                rep = next_rep
                masses = [d.MassLane(next_pre_shift, next_pro_shift, next_msms)]
                has_data = True
                active_measurement = build_mgroup_name(next_m_id, pre, pro)
            row_idx += 1
    return has_data, collected_m_ids
