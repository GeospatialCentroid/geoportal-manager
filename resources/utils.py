from pyproj import Proj, transform
from pyproj import CRS
def get_extent(extent,spatial_reference=False):
    '''
    get the extent and reproject if needed
    It's a bit slow so only start this if you don't mind waiting
    :param extent:
    :return:
    '''

    _extent = get_extent_xyxy(extent)
    inProj = None
    if 'spatialReference' in extent:
        try:
            if 'latestWkid' in extent['spatialReference']:
                projection = str(extent['spatialReference']['latestWkid'])
                if projection != '4326':
                    inProj = CRS('EPSG:' + projection)

            elif 'wkt' in extent['spatialReference']:
                # custom

                inProj = CRS(extent['spatialReference']['wkt'])
            else:

                inProj = CRS(extent['spatialReference'])

        except:
            _extent = None

    if spatial_reference:
        try:
            if spatial_reference.isnumeric():
                # inProj = CRS('EPSG:' + spatial_reference)
                # issue with EPSG 26913 - converts -105.8545,40.3747,-104.6377,40.8414 to ENVELOPE(-109.4896922872799,-109.48968133320209,0.0003683682549243069,0.00036415449139860437)
                print(spatial_reference,"not applied")
            else:
                inProj = CRS(spatial_reference)
        except:
            pass

    if inProj is not None:
        outProj = CRS('EPSG:4326')
        _extent[0], _extent[1] = transform(inProj, outProj, _extent[0], _extent[1], always_xy=True)
        _extent[2], _extent[3] = transform(inProj, outProj, _extent[2], _extent[3], always_xy=True)

    print("The extent was", extent)
    print("The extent is",_extent)

    return _extent


def get_extent_xyxy(extent):
    # convert from "extent": [[minX, minY],[maxX, maxY]],
    # to minX, minY, maxX, maxY
    round_amt=12
    extent_list = []
    try:
        if len(extent) > 1:
            extent_list.append(round(extent[0][0],round_amt))
            extent_list.append(round(extent[0][1],round_amt))
            extent_list.append(round(extent[1][0],round_amt))
            extent_list.append(round(extent[1][1],round_amt))
    except:
        # make exception for the record layers having a different format
        extent_list = [round(extent['xmin'],round_amt), round(extent['ymin'],round_amt), round(extent['xmax'],round_amt), round(extent['ymax'],round_amt)]

    return extent_list