import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

void main() => runApp(MyApp());

class MyApp extends StatelessWidget{
  @override
  Widget build(BuildContext context) => MaterialApp(
    theme: ThemeData.dark(),
    home: MapPage(),
  );
}

class MapPage extends StatefulWidget{
  @override
  _MapPageState createState() => _MapPageState();
}

class _MapPageState extends State<MapPage>{
  final MapController _mc = MapController();
  final TextEditingController _tc = TextEditingController();
  bool showCities = true;
  bool showBorders = false;
  LatLng? _searchMarker;

  // built-in cities (same sample as web)
  final List<Map<String,dynamic>> cities = [
    {"name":"New York, USA","coords": LatLng(40.7128,-74.0060),"pop":"8.4M"},
    {"name":"London, UK","coords": LatLng(51.5074,-0.1276),"pop":"9.0M"},
    {"name":"Tokyo, Japan","coords": LatLng(35.6895,139.6917),"pop":"14M"},
    {"name":"Nairobi, Kenya","coords": LatLng(-1.2921,36.8219),"pop":"4.4M"},
    {"name":"Kampala, Uganda","coords": LatLng(0.3476,32.5825),"pop":"1.7M"},
    {"name":"Sydney, Australia","coords": LatLng(-33.8688,151.2093),"pop":"5.3M"},
    {"name":"Paris, France","coords": LatLng(48.8566,2.3522),"pop":"2.1M"},
    {"name":"Cairo, Egypt","coords": LatLng(30.0444,31.2357),"pop":"9.5M"},
    {"name":"Beijing, China","coords": LatLng(39.9042,116.4074),"pop":"21M"},
    {"name":"Moscow, Russia","coords": LatLng(55.7558,37.6173),"pop":"12.5M"},
    {"name":"Rio de Janeiro, Brazil","coords": LatLng(-22.9068,-43.1729),"pop":"6.7M"},
  ];

  // For borders: we'll attempt to fetch a GeoJSON (can be heavy). We'll parse polygons and build polygon layers.
  final String countriesGeoJsonUrl = 'https://raw.githubusercontent.com/johan/world.geo.json/master/countries.geo.json';
  List<Polygon> countryPolygons = [];

  Future<void> fetchAndParseBorders() async {
    try {
      final res = await http.get(Uri.parse(countriesGeoJsonUrl));
      if(res.statusCode != 200) throw 'failed';
      final js = jsonDecode(res.body);
      final features = js['features'] as List<dynamic>;
      List<Polygon> polygons = [];
      for(final f in features){
        final geom = f['geometry'];
        if(geom == null) continue;
        final type = geom['type'];
        final coords = geom['coordinates'];
        // handle MultiPolygon and Polygon
        if(type == 'Polygon') {
          for(final ring in coords) {
            final points = <LatLng>[];
            for(final pair in ring) {
              final lon = (pair[0] as num).toDouble();
              final lat = (pair[1] as num).toDouble();
              points.add(LatLng(lat, lon));
            }
            polygons.add(Polygon(points: points, color: Colors.transparent, borderStrokeWidth: 1.0, borderColor: Color(0xff6dd3ff)));
          }
        } else if(type == 'MultiPolygon') {
          for(final poly in coords) {
            for(final ring in poly) {
              final points = <LatLng>[];
              for(final pair in ring) {
                final lon = (pair[0] as num).toDouble();
                final lat = (pair[1] as num).toDouble();
                points.add(LatLng(lat, lon));
              }
              polygons.add(Polygon(points: points, color: Colors.transparent, borderStrokeWidth: 1.0, borderColor: Color(0xff6dd3ff)));
            }
          }
        }
      }
      setState(() {
        countryPolygons = polygons;
      });
    } catch(e) {
      print('Error loading borders: $e');
    }
  }

  @override
  void initState(){
    super.initState();
    // fetch borders lazily (heavy)
    // we won't fetch unless user toggles showBorders
  }

  Future<void> search(String q) async {
    final url = Uri.parse('https://nominatim.openstreetmap.org/search?format=json&q=${Uri.encodeComponent(q)}&limit=1');
    final r = await http.get(url, headers: {'Accept':'application/json'});
    final js = jsonDecode(r.body);
    if(js == null || js.length == 0) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Not found')));
      return;
    }
    final item = js[0];
    final lat = double.parse(item['lat']);
    final lon = double.parse(item['lon']);
    setState(()=> _searchMarker = LatLng(lat, lon) );
    _mc.move(LatLng(lat,lon), 5);
    // if a country found and boundingbox exists we can't easily fitBounds here, so we set zoom
  }

  @override
  Widget build(BuildContext ctx){
    return Scaffold(
      appBar: AppBar(
        title: Text('MapBuilder'),
        actions: [
          Row(children:[
            Text('Cities', style: TextStyle(fontSize:14)),
            Switch(value: showCities, onChanged: (v){ setState(()=> showCities = v); })
          ]),
          SizedBox(width:8),
          Row(children:[
            Text('Borders', style: TextStyle(fontSize:14)),
            Switch(value: showBorders, onChanged: (v) async {
              setState(()=> showBorders = v);
              if(v && countryPolygons.isEmpty) {
                // fetch only when user explicitly turns borders on
                await fetchAndParseBorders();
              }
            })
          ]),
          SizedBox(width:8)
        ],
      ),
      body: Stack(children:[
        FlutterMap(
          mapController: _mc,
          options: MapOptions(center: LatLng(20,0), zoom: 2.0),
          children: [
            TileLayer(urlTemplate: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png', subdomains:['a','b','c']),
            // roads overlay toggle if desired - commented
            if(showCities)
              MarkerLayer(markers: cities.map((c) => Marker(
                point: c['coords'] as LatLng,
                width: 40, height: 40,
                builder: (context) => GestureDetector(
                  onTap: () {
                    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('${c['name']} — pop: ${c['pop']}')));
                  },
                  child: Icon(Icons.location_on, size: 32),
                )
              )).toList()),
            if(_searchMarker != null)
              MarkerLayer(markers: [Marker(point: _searchMarker!, width:36,height:36,builder:(c)=>Icon(Icons.gps_fixed,size:36))]),
            if(showBorders && countryPolygons.isNotEmpty)
              PolygonLayer(polygons: countryPolygons),
          ],
        ),
        Positioned(left:12,top:12,right:12,child:Row(children:[
          Expanded(child: Container(
            padding:EdgeInsets.symmetric(horizontal:8),
            decoration:BoxDecoration(color:Color.fromRGBO(10,12,14,0.7),borderRadius:BorderRadius.circular(8)),
            child: TextField(controller:_tc,style:TextStyle(color:Colors.white),decoration:InputDecoration(border:InputBorder.none,hintText:'Search place or country')),
          )),
          SizedBox(width:8),
          ElevatedButton(onPressed:(){ search(_tc.text); }, child:Text('Go'))
        ]))
      ]),
    );
  }
}
