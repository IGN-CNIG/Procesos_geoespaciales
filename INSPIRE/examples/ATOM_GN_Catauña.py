from src.modules.inspire import AtomService
            
def main() -> None:
        
    # 1. Read features from the service service
    # CATALUÑA
    atom = AtomService(source='https://geoserveis.ide.cat/servei/catalunya/inspire-noms-geografics/atom/inspire-noms-geografics.atom.xml', name='Cataluña')
    #pylint: disable = no-value-for-parameter
    features = atom.get_feature(typeNames='NamedPlace')
    print(len(list(features))) # This already consumes the Generator so the next time we use it, it will be empty
    for index, feature in enumerate(features):
        # Here we do something with the features as they get yielded from the ATOM service.
        print(feature)


if __name__ == '__main__':
    main()