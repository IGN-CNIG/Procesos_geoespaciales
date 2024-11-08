WFS_PARAMETERS = {
    '1.0.0': {    
        'service': {
            'description': 'Service name. Value is WFS.',
            'type': 'String',
            'required': True
            },
        'request': {
            'description': 'Operation name.',
            'type': 'String',
            'required': True
        },
        'version': {
            'description': 'Service version. Value is 1.0.0',
            'type': 'String',
            'required': False
            },
        'typeName': {
            'description': 'The typeName parameter determines the collection of feature instances to return.',
            'type': 'String',
            'required': False
            },
        'featureID': {
            'description': 'This parameter is used to filter the features returned by the request.',
            'type': 'String',
            'required': False
            },
        'outputFormat': {
            'description': 'Specifies the format used to encode resources in the response to a query operation. With WFS 2.0, the default outputFormat is “application/gml+xml; version=3.2”.',
            'type': 'String',
            'required': False
            },
        'resultType': {
            'description': 'A WFS can respond to a query operation in one of two ways: It may either generate a complete response document containing resources that satisfy the operation (results) or it may simply generate an empty response container that indicates the count of the total number of resources that the operation would return (hits). With WFS 2.0, the default resultType is results',
            'type': 'String',
            'required': False
            },
        'propertyName': {
            'description': 'This parameter returns feature instances with only the specified property included.',
            'type': 'String',
            'required': False
            },
        'maxFeatures': {
            'description': 'The number to limit the response by is determined by the value of the count parameter.',
            'type': 'Integer',
            'required': False
            },
        'srsName': {
            'description': 'This parameter is used to specify the spatial reference system to encode feature geometries in. The spatial reference systems allowed for each feature type can be identified from the GetCapabilities response.',
            'type': 'String',
            'required': False
            },
        'filter': {
            'description': 'Its value is an XML encoded filter as specified in ISO 19143, Clause 7.',
            'type': 'String',
            'required': False
            },
        'bbox': {
            'description': 'This parameter is a comma-separated list of four numbers that indicate the minimum and maximum bounding coordinates of the feature instances that should be returned.',
            'type': 'String',
            'required': False
            },
        'sortBy': {
            'description': ' This parameter returns feature instances in a sequence determined by the specified parameter.',
            'type': 'String',
            'required': False
            },
    },
    '1.1.0': {    
        'service': {
            'description': 'Service name. Value is WFS.',
            'type': 'String',
            'required': True
            },
        'request': {
            'description': 'Operation name.',
            'type': 'String',
            'required': True
        },
        'version': {
            'description': 'Service version. Value is 1.1.0',
            'type': 'String',
            'required': False
            },
        'typeName': {
            'description': 'The typeName parameter determines the collection of feature instances to return.',
            'type': 'String',
            'required': False
            },
        'featureID': {
            'description': 'This parameter is used to filter the features returned by the request.',
            'type': 'String',
            'required': False
            },
        'outputFormat': {
            'description': 'Specifies the format used to encode resources in the response to a query operation. With WFS 2.0, the default outputFormat is “application/gml+xml; version=3.2”.',
            'type': 'String',
            'required': False
            },
        'resultType': {
            'description': 'A WFS can respond to a query operation in one of two ways: It may either generate a complete response document containing resources that satisfy the operation (results) or it may simply generate an empty response container that indicates the count of the total number of resources that the operation would return (hits). With WFS 2.0, the default resultType is results',
            'type': 'String',
            'required': False
            },
        'propertyName': {
            'description': 'This parameter returns feature instances with only the specified property included.',
            'type': 'String',
            'required': False
            },
        'maxFeatures': {
            'description': 'The number to limit the response by is determined by the value of the count parameter.',
            'type': 'Integer',
            'required': False
            },
        'srsName': {
            'description': 'This parameter is used to specify the spatial reference system to encode feature geometries in. The spatial reference systems allowed for each feature type can be identified from the GetCapabilities response.',
            'type': 'String',
            'required': False
            },
        'filter': {
            'description': 'Its value is an XML encoded filter as specified in ISO 19143, Clause 7.',
            'type': 'String',
            'required': False
            },
        'bbox': {
            'description': 'This parameter is a comma-separated list of four numbers that indicate the minimum and maximum bounding coordinates of the feature instances that should be returned.',
            'type': 'String',
            'required': False
            },
        'sortBy': {
            'description': ' This parameter returns feature instances in a sequence determined by the specified parameter.',
            'type': 'String',
            'required': False
            },
    },
    '2.0.0': {    
        'service': {
            'description': 'Service name. Value is WFS.',
            'type': 'String',
            'required': True
            },
        'request': {
            'description': 'Operation name.',
            'type': 'String',
            'required': True
        },
        'version': {
            'description': 'Service version. Value is 2.0.0',
            'type': 'String',
            'required': False
            },
        'typeNames': {
            'description': 'The typeNames parameter determines the collection of feature instances to return.',
            'type': 'String',
            'required': False
            },
        'resourceID': {
            'description': 'This parameter is used to filter the features returned by the request.',
            'type': 'String',
            'required': False
            },
        'outputFormat': {
            'description': 'Specifies the format used to encode resources in the response to a query operation. With WFS 2.0, the default outputFormat is “application/gml+xml; version=3.2”.',
            'type': 'String',
            'required': False
            },
        'resultType': {
            'description': 'A WFS can respond to a query operation in one of two ways: It may either generate a complete response document containing resources that satisfy the operation (results) or it may simply generate an empty response container that indicates the count of the total number of resources that the operation would return (hits). With WFS 2.0, the default resultType is results',
            'type': 'String',
            'required': False
            },
        'propertyName': {
            'description': 'This parameter returns feature instances with only the specified property included.',
            'type': 'String',
            'required': False
            },
        'count': {
            'description': 'The number to limit the response by is determined by the value of the count parameter.',
            'type': 'Integer',
            'required': False
            },
        'srsName': {
            'description': 'This parameter is used to specify the spatial reference system to encode feature geometries in. The spatial reference systems allowed for each feature type can be identified from the GetCapabilities response.',
            'type': 'String',
            'required': False
            },
        'filter': {
            'description': 'Its value is an XML encoded filter as specified in ISO 19143, Clause 7.',
            'type': 'String',
            'required': False
            },
        'bbox': {
            'description': 'This parameter is a comma-separated list of four numbers that indicate the minimum and maximum bounding coordinates of the feature instances that should be returned.',
            'type': 'String',
            'required': False
            },
        'sortBy': {
            'description': ' This parameter returns feature instances in a sequence determined by the specified parameter.',
            'type': 'String',
            'required': False
            },
    }
}

WCS_PARAMETERS = {
    '1.0.0': {
        'service': {
            'description': 'Service name: Value is WCS.',
            'type': 'String',
            'required': True
            },
        'request': {
            'description': 'Operation name.',
            'type': 'String',
            'required': True
        },
        'version': {
            'description': 'Service version. Value is 1.0.0',
            'type': 'String',
            'required': True
        },
        'coverage': {
            'description': 'Name of an available coverage.',
            'type': 'String',
            'required': True
        },
        'crs': {
            'description': 'Coordinate Reference System in which the request is expressed.',
            'type': 'String',
            'required': True
        },
        'response_crs': {
            'description': 'Coordinate Reference System in which to express coverage responses. Defaults to the request CRS.',
            'type': 'String',
            'required': False
        },
        'bbox': {
            'description': 'Request a subset defined by the specified bounding box, with min/max coordinate pairs ordered according to the Coordinate Reference System identified by the CRS parameter. One of BBOX or TIME is required.',
            'type': 'String',
            'required': False
        },
        'time': {
            'description': 'Request a subset corresponding to the specified time instants or intervals, expressed in an extended ISO 8601 syntax. Optional if a default time (or fixed time, or no time) is defined for the selected layer. One of BBOX or TIME is required.',
            'type': 'String',
            'required': False
        },
        'width': {
            'description': 'Width of the grid (number of grid points). Either WIDTH and HEIGHT or RESX and RESY are required.',
            'type': 'Integer',
            'required': False
        },
        'height': {
            'description': 'Height of the grid (number of grid points). Either WIDTH and HEIGHT or RESX and RESY are required.',
            'type': 'Integer',
            'required': False
        },
        'depth': {
            'description': 'Depth of the grid (number of grid points) for 3D coverages. Either WIDTH, HEIGHT, and DEPTH or RESX, RESY, and RESZ are required for 3D grids.',
            'type': 'Integer',
            'required': False
        },
        'RESX': {
            'description': 'Spatial resolution along the X axis (in units appropriate to the CRS). Either RESX and RESY or WIDTH and HEIGHT are required.',
            'type': 'Double',
            'required': False
        },
        'RESY': {
            'description': 'Spatial resolution along the Y axis (in units appropriate to the CRS). Either RESX and RESY or WIDTH and HEIGHT are required.',
            'type': 'Double',
            'required': False
        },
        'RESZ': {
            'description': 'Spatial resolution along the Z axis for 3D grids (in units appropriate to the CRS). Either RESX, RESY, and RESZ or WIDTH, HEIGHT, and DEPTH are required.',
            'type': 'Double',
            'required': False
        },
        'interpolation': {
            'description': 'Interpolation method for resampling coverage values (e.g., nearest, bilinear). Defaults to server-defined method.',
            'type': 'String',
            'required': False
        },
        'format': {
            'description': 'Requested output format for the coverage (e.g., image/tiff, application/x-netcdf).',
            'type': 'String',
            'required': True
        },
        'exceptions': {
            'description': 'Format for reporting exceptions.',
            'type': 'String',
            'required': False
        }
    },
    '2.0.1': {
        'service': {
            'description': 'Service name: Value is WCS.',
            'type': 'String',
            'required': True
        },
        'request': {
            'description': 'Operation name. Value is GetCoverage.',
            'type': 'String',
            'required': True
        },
        'version': {
            'description': 'Service version. Value is 2.0.1.',
            'type': 'String',
            'required': True
        },
        'coverageID': {
            'description': 'The unique identifier of the coverage being requested.',
            'type': 'String',
            'required': True
        },
        'format': {
            'description': 'The requested output format for the coverage (e.g., image/tiff, application/x-netcdf).',
            'type': 'String',
            'required': True
        },
        'subset': {
            'description': 'Defines the spatial and/or temporal bounding box or slices for the desired subset of the coverage. It is used to specify the portion of the coverage you want to retrieve. Defined by axes such as Long, Lat, Time.',
            'type': 'List of Strings',
            'required': True
        },
        'rangeSubset': {
            'description': 'Specifies the range subset of the coverage, such as specific bands or fields (e.g., specific bands in a multispectral image).',
            'type': 'String',
            'required': False
        },
        'outputCRS': {
            'description': 'Specifies the Coordinate Reference System (CRS) in which to express the output coverage.',
            'type': 'String',
            'required': False
        },
        'resolution': {
            'description': 'The spatial resolution of the requested coverage. Can be expressed along each axis (e.g., x, y, [z] for 3D).',
            'type': 'List of Doubles',
            'required': False
        },
        'interpolation': {
            'description': 'Specifies the interpolation method for resampling the coverage values (e.g., nearest, bilinear). Defaults to server-defined method.',
            'type': 'String',
            'required': False
        },
        'mediaType': {
            'description': 'Specifies the media type for the output.',
            'type': 'String',
            'required': False
        },
        'exceptions': {
            'description': 'Specifies the format for reporting exceptions.',
            'type': 'String',
            'required': False
        }
    }
}
