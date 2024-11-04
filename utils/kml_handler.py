from pykml import parser

def kml_reader(kml_files):
    aoi_names, aois = [], []
    for kml in kml_files:
        with open('roi/' + kml, 'r') as f:
            root = parser.parse(f).getroot()
        namespace = {"kml": 'http://www.opengis.net/kml/2.2'}
        pms = root.xpath(".//kml:Placemark[.//kml:Polygon]", namespaces=namespace)
        roi_string = []
        for p in pms:
            if hasattr(p, 'MultiGeometry'):
                for poly in p.MultiGeometry.Polygon:
                    roi_string.append(poly.outerBoundaryIs.LinearRing.coordinates)
            else:
                roi_string.append(p.Polygon.outerBoundaryIs.LinearRing.coordinates)

        dot = kml_files[0].find('.')
        name_kml = kml_files[0][:dot] + '-'
        for jdx, r in enumerate(roi_string):
            aoi_names.append(name_kml + str(jdx))
            roi_str = str(r).split(' ')
            aux = []
            for idx, rs in enumerate(roi_str):
                if idx == 0:
                    n = rs[7::].split(',')
                    aux.append([float(n[i]) for i in range(len(n)-1)])
                elif idx == (len(roi_str)-1): 
                    print(rs)
                else:
                    n = rs.split(',')
                    aux.append([float(n[i]) for i in range(len(n)-1)])
            aois.append([aux])

    return aoi_names, aois
