var geoJSON = [];
var latlngs = [];
var bounds = [[42.34, -71.113], [42.44, -71.09]];
var LineStringOpt = {color : 'green', opacity : 0.5, weight : 8};
var paths = [];
var markers = [];
var accessToken = 'pk.eyJ1IjoiZ2F1cmF2OTE2IiwiYSI6IjQ1MTQyMzliYzRkM2JiMWZhNzc5N2I0Nzg4NzhkMWYwIn0.ijhVLyeyp8i8G5g6FkvbQg';
var message = '';

function Load() {
    // Initialize MapBox map<script>
    L.mapbox.accessToken = accessToken;
    map = L.mapbox.map('map', 'gaurav916.6e4f51b4').setView([42.373, -71.103], 13);
};


function ShowLoading(showLoading) {
    if (showLoading) {
        $('#loading').css('visibility', 'visible');
    } else {
        $('#loading').css('visibility', 'hidden');
    };
};

function ResetMap(){
    // Reset pan and zoom
    geoJSON = [];
    map.featureLayer.setGeoJSON(geoJSON);
    map.fitBounds(bounds);

    // Click on markers to Google Search
    map.featureLayer.on('click', function(e) {
      window.open(e.layer.feature.properties.url);
  });

};

// The Following Section Finds Your Route
function FindAndRoute(startPt, endPt, runDis){
   ShowLoading(true);
   message = '';
   $('#addmessage').html(message);
   $.getJSON('/findRoute', {'s': startPt,'e': endPt,'d':runDis}, function(findJSON){         
          // Maybe reset on bad query
          ShowLoading(false);
          //console.log(findJSON);
          //console.log(jQuery.isEmptyObject(findJSON));
          if (!jQuery.isEmptyObject(findJSON)) {  
          //if (findJSON!={}) {              
             console.log('Path Found');
             message = findJSON['message'];
             $('#addmessage').html(message); 

             // Add geoMarkers to feature llayer
             geoJSON.push(findJSON['path']);
             map.featureLayer.setGeoJSON(geoJSON);

             //Pan and zoom
             map.fitBounds(findJSON['bounds']);
          }else{
             //console.log('Path NOT Found');
             message = 'Path not found! Please check your address, and make sure they are within the blue boundary of Cambridge and Boston.'; 
             //console.log(message);
             $('#addmessage').html(message);
          }
   });      
};

function PathSearch() {
    // Grab address box valuePathTestMashUp
    var startPt = $('#startPt').val();
    console.log('Inside PathSearch');
    console.log(startPt);
    var endPt = $('#endPt').val();
    console.log(endPt);
    var runDis = $('#runDist').val();
    console.log(runDis);
    // Reset map ...
    ResetMap();
    // If it is not empty ...
    if (endPt == 'default = start') {
        // ... and find and route
        document.getElementById("endPt").value=document.getElementById("startPt").value;
        FindAndRoute(startPt, startPt, runDis);//FIXME: no runLoop fun implemented yet
    }else{
        console.log('prepare to run find and route');
        FindAndRoute(startPt, endPt, runDis);
    }
	
};

