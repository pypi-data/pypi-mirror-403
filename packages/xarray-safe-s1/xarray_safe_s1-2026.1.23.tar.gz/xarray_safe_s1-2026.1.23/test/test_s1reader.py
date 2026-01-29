import logging

from safe_s1 import Sentinel1Reader, getconfig, sentinel1_xml_mappings

logging.basicConfig()
logging.captureWarnings(True)

logger = logging.getLogger("s1_reader_test")
logger.setLevel(logging.DEBUG)

conf = getconfig.get_config()
products = [
    sentinel1_xml_mappings.get_test_file(filename) for filename in conf["product_paths"]
]


# Try to apply the reader on different products
def test_reader():
    try:
        for product in products:
            reader = Sentinel1Reader(product)
            # When a product is a multidataset, datatree is none, so we want to be sure that the datatree isn't empty
            # (selecting a dataset)
            sub_reader = Sentinel1Reader(reader.datasets_names[0])
            dt = sub_reader.datatree
            for ds in dt:
                dt[ds].to_dataset().compute()
        assert True
    except IOError:
        assert False
