from src.modules.inspire import WFSService
from src.utils.utils import month_ranges


def main() -> None:
        
    # 1. Read features from the service service
    ranges = month_ranges('2004-01-01', '2024-09-16')
    
    # Aragón
    # NOTE: THE PAGING IS NOT WORKING YET, IT ONLY FETCHES 100 ROWS OUT OF THE WHOLE DATABASE
    # NOTE: They didn't fix the beginLifespanVersion update, so every time they update the database the property is set to that date in every feature
    name = 'Andalucia'
    wfs = WFSService(source='https://idearagon.aragon.es/inspireIdearagon/services/wfsGN', name=name, version='2.0.0', max_features=5000, timeout=90)
    
    def get_features(ranges):
        for month_range in ranges:
            begin = month_range[0].isoformat()
            end = month_range[1].isoformat()
            response = wfs.get_feature(typeNames='gn:NamedPlace', srsName='EPSG:25830', SQL_PREDICATE=f"beginLifespanVersion >= '{begin}' and beginLifespanVersion < '{end}'")
            yield from response # response is a Generator, we yield all features from it
    
    features = get_features(ranges)
    print(len(list(features)))


if __name__ == '__main__':
    main()