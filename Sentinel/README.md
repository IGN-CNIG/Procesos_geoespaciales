# Introducción

Se desea desarrollar un visualizador cartográfico para el Área de Teledetección del Instituto Geográfico Nacional en el que se muestren las imágenes de los satélites de monitoreo de la superficie terrestre Sentinel-2. Sentinel-2 es una misión de Observación del Territorio impulsada por la Agencia Espacial Europea, que forma parte del programa Copernicus.

Estos datos son de acceso libre y gratuito, y solo se necesita una cuenta gratuita en la plataforma de Copernicus Data Space Ecosystem: [Copernicus Data Space Ecosystem Registration](https://documentation.dataspace.copernicus.eu/Registration.html).

Una vez creada la cuenta, se obtendrán las credenciales necesarias para la autenticación. Las credenciales para acceder a estos datos incluyen:

- **Client ID**: Identificador del cliente.
- **Client Secret**: Clave secreta del cliente.

Las imágenes capturadas por Sentinel-2 comprenden 13 bandas espectrales, a resoluciones de 10, 20 y 60 metros dependiendo de la banda espectral, lo que permite un análisis detallado de la superficie terrestre. Además, se proporciona una cobertura cada 5 días con ambos satélites, lo que permite un monitoreo continuo.

| Banda   | Longitud de onda (nm) | Resolución espacial (m) | Descripción / Aplicación                                        |
|---------|-----------------------|-------------------------|-----------------------------------------------------------------|
| Banda 1 | 443                   | 60                      | Aerosol costero (monitoreo de aerosoles y turbidez)             |
| Banda 2 | 490                   | 10                      | Azul (mapeo de cuerpos de agua / penetración de agua)           |
| Banda 3 | 560                   | 10                      | Verde (evaluación de la vegetación / mapeo de vegetación)       |
| Banda 4 | 665                   | 10                      | Rojo (diferenciación de la vegetación / análisis de vegetación) |
| Banda 5 | 705                   | 20                      | Infrarrojo cercano (NIR) de banda estrecha (evaluación de la vegetación y estructura del dosel) |
| Banda 6 | 740                   | 20                      | Infrarrojo cercano (NIR) de banda estrecha (detección del vigor de la vegetación) |
| Banda 7 | 783                   | 20                      | Infrarrojo cercano (NIR) de banda estrecha (mapeo de la clorofila y estudios de vegetación) |
| Banda 8 | 842                   | 10                      | Infrarrojo cercano (NIR) (análisis de vegetación y uso del suelo) |
| Banda 8A| 865                   | 20                      | Infrarrojo cercano (NIR) de banda estrecha (detalles de la vegetación) |
| Banda 9 | 945                   | 60                      | Infrarrojo cercano (NIR) (detección de vapor de agua y corrección atmosférica) |
| Banda 10| 1375                  | 60                      | Infrarrojo de onda corta (SWIR) (detección de nubes y vapor de agua) |
| Banda 11| 1610                  | 20                      | Infrarrojo de onda corta (SWIR) (detección de humedad del suelo / nieve y hielo) |
| Banda 12| 2190                  | 20                      | Infrarrojo de onda corta (SWIR) (análisis de incendios / mapeo de la vegetación seca y humedad del suelo) |

Para alimentar el visualizador de imágenes Sentinel-2, se ha creado el proceso que se describirá detalladamente a lo largo de este documento.

El objetivo es obtener las teselas Sentinel más recientes que cumplan determinados criterios de búsqueda:

- **Cobertura de nubes inferior al 5%**
- **Producto S2MSI2A**: Este producto es un dato de nivel 2A generado por el MultiSpectral Instrument (MSI) del satélite Sentinel-2. El nombre "S2MSI2A" se desglosa de la siguiente manera:
  - **S2**: Sentinel-2
  - **MSI**: MultiSpectral Instrument
  - **2A**: Nivel de procesamiento 2A

    *Nota*: Los productos de nivel 2A están corregidos atmosféricamente. Esto significa que se han aplicado correcciones para remover efectos atmosféricos, proporcionando imágenes en la superficie de la Tierra que pueden ser más fácilmente interpretadas en términos de características terrestres.

- **Tesela Sentinel-2**: Sentinel-2 utiliza un sistema de cuadrícula militar para definir el mosaico de imágenes satélite. La búsqueda se centrará en las teselas correspondientes al territorio nacional.

A estas teselas se les aplicarán los siguientes procesos para obtener el producto final:

1. **Filtrado de bandas para obtener dos productos:**
   - Imagen en color natural (RGB)
   - Imagen en falso color natural (NirGB)
   
   *Nota*: Todas las bandas necesarias para obtener estos productos tienen una resolución de 10 metros, por lo que no es necesario su remuestreo.

2. **Cambio de Sistema de Referencia** para obtener una imagen georreferenciada en el SRG deseado.

3. **Ajustes de brillo y contraste** según la estación y la combinación de bandas.

# Ámbito Geográfico

Para la selección y análisis de datos de imágenes de satélite Sentinel-2, hemos focalizado nuestra búsqueda en las teselas correspondientes al territorio nacional. El sistema de teselado utilizado para estos productos está basado en una malla global, diseñada específicamente para los productos Harmonized Landsat and Sentinel-2 (HLS).

*Nota*: Para saber más sobre la malla utilizada en los productos Sentinel-2, utilice el siguiente enlace [HLS Tiling System](https://hls.gsfc.nasa.gov/products-description/tiling-system/).

# Acceso a datos y procesamiento

## Búsqueda en el catálogo de datos

En primer lugar, se utiliza un cliente STAC para buscar y filtrar imágenes satelitales basadas en criterios como la cobertura de nubes, el área geográfica de interés y el rango temporal.

El servicio STAC (SpatioTemporal Asset Catalog) es un estándar abierto para la catalogación de datos espaciales y temporales, diseñado para hacer que la búsqueda y el acceso a datos geoespaciales sean más eficientes. Una API STAC es una interfaz de programación de aplicaciones que sigue el estándar STAC para acceder, buscar y gestionar conjuntos de datos geoespaciales a través de la web.

Una API STAC permite realizar operaciones típicas como:

- **Búsqueda**: Buscar catálogos, colecciones, y elementos (que son los datos geoespaciales individuales) usando parámetros como ubicación, tiempo, y propiedades específicas.
- **Acceso a metadatos**: Obtener información sobre los datos, como la cobertura espacial, la fecha de adquisición, y las propiedades asociadas.
- **Descarga**: Acceder a enlaces para descargar los datos o para consultar servicios adicionales.

La API STAC de Copernicus es accesible a través del siguiente enlace: [STAC API Copernicus](https://catalogue.dataspace.copernicus.eu/stac/).

Más información: [STAC API Documentation](https://documentation.dataspace.copernicus.eu/APIs/STAC.html#items-search-in-a-stac-collection).

## Descarga de imágenes COG

Para la descarga de los datos se utiliza el objeto datacube, que es una estructura multidimensional que organiza grandes volúmenes de datos geoespaciales en un formato uniforme y accesible. En el contexto de datos de satélites, un datacube generalmente incluye:

- **Dimensiones Espaciales**: Las coordenadas geográficas (longitud y latitud).
- **Dimensión Temporal**: El tiempo en que se tomaron las imágenes.
- **Dimensiones Espectrales**: Las bandas espectrales de las imágenes.

Un datacube permite realizar operaciones complejas de análisis en grandes conjuntos de datos, como calcular índices de vegetación a lo largo del tiempo o combinar diferentes bandas espectrales en una sola imagen.

### Reproyección al Sistema de Referencia deseado

Los archivos COG (Cloud Optimized GeoTIFF) de las imágenes Sentinel-2 están generalmente en el sistema de referencia de coordenadas (CRS) UTM (Universal Transverse Mercator). Cada imagen de Sentinel-2 está proyectada en una de las zonas UTM, y el CRS específico utilizado es una de las variantes del EPSG:326XX o EPSG:327XX, dependiendo de la latitud:

- **EPSG:326XX**: Utilizado para zonas UTM en el hemisferio norte.
- **EPSG:327XX**: Utilizado para zonas UTM en el hemisferio sur.

El método `resample_spatial` del datacube se utiliza principalmente para cambiar la resolución espacial, pero también permite especificar un nuevo CRS al que los datos deben ser re-proyectados. Cuando se cambia el CRS, se transforman las coordenadas de todos los píxeles en el datacube al nuevo sistema de referencia espacial.

### Filtrado de bandas para obtener las imágenes RGB y NirGB

El método `filter_bands` del datacube permite seleccionar las bandas específicas de interés en el datacube.

### Descarga de imágenes en formato COG

El método `download` del datacube permite ejecutar el procesamiento de los datos y descargar el archivo. Para la exportación del archivo georreferenciado y la descarga del archivo COG, se utiliza el plugin `gdal`.

## Ajuste de brillo y contraste

Para ajustar el brillo y el contraste de las imágenes descargadas según la estación del año y la combinación de bandas, se aplica un realce de contraste utilizando una técnica similar a la de "StretchToMinimumMaximum" de QGIS, y luego se convierte la imagen de 16 bits a 8 bits para su visualización. Este tipo de procesamiento es común en el análisis de imágenes de satélite, donde se necesita mejorar la visibilidad de ciertos detalles al ajustar los valores de píxel para maximizar el rango dinámico visible.

Dirante este proceso se utilizan técnicas de mejora de imagen que implican:
- **Normalización**: Ajustar los valores de los píxeles a un rango estándar.
- **Ecualización de histograma**: Redistribuir los valores de los píxeles para mejorar el contraste de la imagen.
- **Clipping**: Recortar valores extremos de brillo y contraste

```python
apply_contrast_enhancement(input_file=file_path, output_dir=PROJECT_DIR, suffix=suffix, area_name=tileset.name, date=metadata['start_datetime'])
```

Para realizar este realce de contraste se abre la imagen utilizando la librería GDAL, y se siguen los siguientes pasos:

1. **Se calculan los valores mínimos y máximos** que se van a utilizar para mejorar el contraste de la imagen. Estos límites se determinan eliminando los valores extremos (2% más bajos y 2% más altos) que podrían distorsionar el contraste.

2. **Usando los límites calculados**, se ajusta cada banda de la imagen para estirar los valores de los píxeles dentro del nuevo rango. Esto hace que los detalles sean más visibles al mejorar el contraste.

3. **Se convierte la imagen ajustada de 16 bits a 8 bits**. Esto implica reducir el rango de valores de los píxeles (de [-32768, 32767] a [0, 255]) para que sea más fácil de manejar y visualizar en pantallas y software estándar.

4. **Finalmente, se guarda la nueva imagen mejorada y convertida en 8 bits en un archivo de salida.**

# API de visualización

El servicio de visualización responsable de servir imágenes y los metadatos asociados desde el sistema de archivos del servidor será un servicio WMS conforme a la Directiva Inspire. 
El repositorio de imágenes del WMS se actualizará de forma automatizada gracias a la implementación de un servicio que se ejecutará periódicamente. Las imágenes se han tratado con Python y GDAL para servirlas en un formato optimizado para web, **Cloud Optimized GeoTIFF (COG)**, por lo que están listas para su publicación a través de un visualizador cartográfico.

Para la visualización de los datos a través de la web se creará un visualizador cartográfico empleando la [API-CNIG](https://plataforma.idee.es/en/cnig-api) como base para el desarrollo.

# Conclusión

La implementación de este visualizador cartográfico proporcionará una herramienta valiosa para el monitoreo y análisis de la superficie terrestre a través de imágenes de satélite Sentinel-2. Al optimizar la recuperación, el procesamiento y la visualización de datos, se maximizará la utilidad de los recursos disponibles para los usuarios del Instituto Geográfico Nacional y otros interesados en la teledetección y análisis de datos geoespaciales.