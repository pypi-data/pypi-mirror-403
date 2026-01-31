import rpy2.robjects as robjects
import rpy2.robjects.packages as rpackages


def install_isocorrector():
    print("Running IsoCorrector installation", flush=True)
    if rpackages.isinstalled("IsoCorrectoR"):
        print("Found IsoCorrectoR package", flush=True)
    else:
        print("Installing IsoCorrectoR package", flush=True)
        utils = rpackages.importr("utils")
        if not rpackages.isinstalled("BiocManager"):
            utils.install_packages("BiocManager")
        robjects.r('BiocManager::install(pkgs="IsoCorrectoR", ask=FALSE)')
