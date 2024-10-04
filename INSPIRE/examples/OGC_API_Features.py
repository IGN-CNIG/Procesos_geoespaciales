from src.modules.inspire import OGCAPIService
            
def main() -> None:
    
    API = OGCAPIService(source='https://api-coverages.idee.es', name='DTM')
    collections = API.capabilities.get_collections()
    operations = API.capabilities.get_operations()
    collection_params = API.capabilities.get_operation_parameters('/collections/EL.ElevationGridCoverage_4326_1000/coverage')
    collection_queryables = API.capabilities.get_operation_queryables('/collections/EL.ElevationGridCoverage_4326_1000/coverage')
    
    coverage = API.get_coverage(collectionId='EL.ElevationGridCoverage_4326_1000', bbox='-0.952441692352295,38.14093610853549,-0.9505963325500489,38.14208368992904', bbox_crs=4326)
    print(coverage)

    API = OGCAPIService(source='https://api-maps.idee.es', name='Maps')
    collections = API.capabilities.get_collections()
    parameters = API.capabilities.get_operation_parameters('/collections/IGNBaseTodo/map')
    queryables = API.capabilities.get_operation_queryables('/collections/IGNBaseTodo/map')
    collection_description = API.capabilities.describe_collection(collectionId='IGNBaseTodo')
    is_crs84_supported = API.capabilities.is_output_crs_supported(collectionId='IGNBaseTodo', crs='http://www.opengis.net/def/crs/OGC/1.3/CRS84')
    image = API.get_map(collectionId='IGNBaseTodo', bbox='-0.952441692352295,38.14093610853549,-0.9505963325500489,38.14208368992904')
    print(image)
    
        
    # 1. Read features from the service service
    # OGC API Address
    API = OGCAPIService(source='https://api-features.idee.es', name='Address')
    collections = API.capabilities.get_collections()
    operation_parameters = API.capabilities.get_operation_parameters('/collections/address/items')
    operation_queryables = API.capabilities.get_operation_queryables('/collections/address/items')
    
    features = API.get_feature(collectionId='address', crs='http://www.opengis.net/def/crs/EPSG/0/25830', inspireId_localId='AD_ADDRESS_PPK_010010016525')
    print([feature for feature in features])
    
    # OGC API Geographical Names
    API = OGCAPIService(source='https://api-features.ign.es', name='NGBE')
    if 'namedplace' in API.capabilities.get_collections():
        api_parameters = API.capabilities.get_operation_parameters('/collections/namedplace/items')
        print(f'The available parameters for the getFeature request are: {list(api_parameters.keys())}')
        api_queryables = API.capabilities.get_operation_queryables('/collections/namedplace/items')
        print(f'The queryable queryables for the getFeature request are: {list(api_queryables.keys())}')
        # 1. Fetch just one feature by its label
        features1 = API.get_feature(collectionId='namedplace', crs='http://www.opengis.net/def/crs/EPSG/0/25830', etiqueta='Punta do Limo')
        for feature in features1:
            print(feature)
        # 2. Fetch all fetaures
        features2 = API.get_feature(collectionId='namedplace', crs='http://www.opengis.net/def/crs/EPSG/0/25830')
        num_features = 0
        for feature in features2:
            num_features += 1
        print(num_features)

    # Cataluña
    # NOTE: describe_collection no está funcionando
    # https://geoserveis.ide.cat/servei/catalunya/inspire/ogc/features/collections/inspire:GN.GeographicalNames?f=application%2Fjson
    
    API = OGCAPIService(source='https://geoserveis.ide.cat/servei/catalunya/inspire/ogc/features', name='Edificios Cataluña')
    if 'inspire:GN.GeographicalNames' in API.capabilities.get_collections():
        api_parameters = API.capabilities.get_parameters()
        print(f'The available parameters for the getFeature request are: {list(api_parameters)}')
        api_queryables = API.capabilities.get_queryables()
        print(f'The queryable queryables for the getFeature request are: {list(api_queryables)}')
        features3 = API.get_feature(collectionId='inspire:GN.GeographicalNames', crs='http://www.opengis.net/def/crs/EPSG/0/25830')
        num_features = 0
        for feature in features3:
            num_features += 1
        print(num_features)


if __name__ == '__main__':
    main()