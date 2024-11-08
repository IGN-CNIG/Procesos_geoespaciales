from src.modules.inspire import WFSService
from src.utils.utils import month_ranges


def main() -> None:
        
    # 1. Read features from the service service

    ranges = month_ranges('2005-03-01', '2005-04-01')
    
    # Andalucía
    # NOTE: THE PAGING IS NOT SET IN THE CAPABILITIES YET, BUT IT IS WORKING AS WE CAN SI IN THIS EXAMPLE
    name = 'Andalucia'
    wfs = WFSService(source='https://www.ideandalucia.es/wfs-nga-inspire/services', name=name, version='2.0.0', max_features=5000, timeout=90)
    
    def get_features(ranges):
        for month_range in month_ranges:
            begin = month_range[0].isoformat()
            end = month_range[1].isoformat()
            response = wfs.get_feature(typeNames='gn:NamedPlace', srsName='EPSG:25830', SQL_PREDICATE=f"beginLifespanVersion >= '{begin}' and beginLifespanVersion < '{end}'")
            yield from response # response is a Generator, we yield all features from it
    
    features = get_features(month_ranges)
    print(len(list(features)))


if __name__ == '__main__':
    main()