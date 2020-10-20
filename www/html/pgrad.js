$(function() {

//http://127.0.0.1:5000/models_avail_page

// works
//  $.get( "http://127.0.0.1:5000/models_avail_page", function(model_data2) {
//    console.log(model_data2);
//  });


  console.log('mark01')

$(function() {
    queryModelsAvail();
    //data = queryModelsAvail();
    //console.log(data)
});

  console.log('mark02')

  function queryModelsAvail () {
    $.get('http://127.0.0.1:5000/models_avail_page', function(data) { 
        console.log(data);
        var table_html = '';
        $.each(data, function (i, item) {
            table_html += '<tr><td style="text-align:center">' + item.model + '</td>\
                               <td style="text-align:center">' + item.dt_init + '</td>\
                               <td style="text-align:center">' + item.hrs_avail + '</td>\
                               <td style="text-align:center">' + item.dt_proc_lt + '</td></tr>';
        });
        //$.each(data, function (i, item) {
        //    table_html += '<tr><td style="text-align:center">' + item.model + '</td><td style="text-align:center">' + item.dt_init + '</td><td style="text-align:center">' + item.hrs_avail + '</td><td style="text-align:center">' + item.dt_proc_lt + '</td></tr>';
        //});
        $('#modelsAvailTable').append(table_html);
    });
    //console.log(data);
    //return(data);
  }

  console.log('mark03')

  console.log('mark04')

  console.log('mark05')

//  function queryModelsAvail() {
//    $.get( "http://127.0.0.1:5000/models_avail_page", function(model_data2) {
//     console.log(model_data2)
//      return model_data2;
//    });
//    return model_data2
//  }

//  console.log('before query')
//  model_data2 = queryModelsAvail();
//  console.log('after query')

//var jsonData = '[{"rank":"9","content":"Alon","UID":"5"},{"rank":"6","content":"Tala","UID":"6"}]';
//var trHTML = '';
//$.each(response, function (i, item) {
//    trHTML += '<tr><td>' + item.rank + '</td><td>' + item.content + '</td><td>' + item.UID + '</td></tr>';
//});
//$('#records_table').append(trHTML);
//


//var myUrl = "http://127.0.0.1:5000/models_avail_page";    
//$.get(myUrl, function(data){
//    //data here will be object, should not used directly
//    $("#statusToggle").html(data);
//    alert("load was performed"); 
//}, 'json');        
       
  $("#statusToggle").click(function(){
        $("table").toggle(50);
    });

  $("#stationMapToggle").click(function(){
        $("img").toggle(50);
    });



  $('.dropdown-menu a').on('click', function(){    
    $(this).parent().parent().prev().html($(this).html()+'<span class="caret"></span>');    
  })

  function createPlotName(plotStnPair, plotModel, plotTimeframe) {
    //var plotName = plotVariable+"_"+plotRegion+"_stn_day_of_vs_time_"+plotTimeframe+".png"
    //ws_foothill_region_day_of_vs_time_current.png
    if (plotModel == "all_8d") {
        var plotTimeframe = "8" // can be 2, 3 or 8 here
        var plotName = "del_slp_all_model_"+plotStnPair+"_current_"+plotTimeframe+".png"
    } else if (plotModel == "all_3d") {
        var plotTimeframe = "3" // can be 2, 3 or 8 here
        var plotName = "del_slp_all_model_"+plotStnPair+"_current_"+plotTimeframe+".png"
    } else if (plotModel == "all_2d") {
        var plotTimeframe = "2" // can be 2, 3 or 8 here
        var plotName = "del_slp_all_model_"+plotStnPair+"_current_"+plotTimeframe+".png"
    } else {
        if (plotModel == "gfs") {var plotTimeframe = "8"}
        else if (plotModel == "nam") {var plotTimeframe = "3"}
        else if (plotModel == "hrrr") {var plotTimeframe = "2"}    
        var plotName = "del_slp_all_init_"+plotStnPair+"_"+plotModel+"_"+plotTimeframe+".png"   
    }
    console.log(plotName);
    return (plotName);
  }

  function createPlotText(plotStnPairText, plotModelText) {
    //var plotText = "Forecast "+plotVariableText+" at "+plotRegionText+" for "+plotTimeframeText
    if (plotModel == "all_model") {
        var plotText = "Forecast pressure difference, "+plotStnPairText+", all models most recent init"
    } else {
        var plotText = "Forecast pressure difference, "+plotStnPairText+", "+plotModelText+" all init"
    }
    console.log(plotText);
    return (plotText);
  }

  function createPlotCdfName(plotStnPair) {
    var plotPlotCdfName = "del_alt_cdf_"+plotStnPair+".png"
    //console.log(plotPlotCdfName);
    return (plotPlotCdfName);
  }

  function createTableName(plotStnPair) {
    var tableName = "del_alt_top_events_"+plotStnPair+".png"
    //console.log(tableName);
    return (tableName);
  }

  function replaceImageAndText(plotStnPair, plotModel, plotStnPairText, plotModelText) {
    plotText    = createPlotText(plotStnPairText, plotModelText);
    plotName    = createPlotName(plotStnPair, plotModel);
    plotCdfName = createPlotCdfName(plotStnPair);
    tableName   = createTableName(plotStnPair);    
    $("#plot_text").text(plotText);
    $("#plot_selected").find('img').attr("src", "../../images/"+plotName);
    $("#plot_cdf").find('img').attr("src", "../../top_events/"+plotCdfName);
    $("#plot_table").find('img').attr("src", "../../top_events/"+tableName);
  }

  var plotStnPair = "KWMC-KSFO";
  var plotModel = "gfs";
  var plotTimeframe = "8";

  var plotStnPairText = "Winnemucca - San Francisco";
  var plotModelText = "GFS";
  var plotTimeframeText = "8 days";
     
  plotName = createPlotName(plotStnPair, plotModel);
  plotText = createPlotText(plotStnPairText, plotModelText);
  plotCdfName = createPlotCdfName(plotStnPair);
  tableName   = createTableName(plotStnPair);

  $("#stn-pills a").on('click', function (event) {
    $(this).parent().toggleClass('open');
    $(this).parent().parent().find(".active").removeClass("active");
    plotStnPair     = $(this).data("value");
    plotStnPairText = $(this).data("text");
    replaceImageAndText(plotStnPair, plotModel, plotStnPairText, plotModelText);
  });

  $("#model-pills a").on('click', function (event) {
    $(this).parent().toggleClass('open');
    $(this).parent().parent().find(".active").removeClass("active");
    plotModel = $(this).data("value");
    plotModelText = $(this).data("text");
    replaceImageAndText(plotStnPair, plotModel, plotStnPairText, plotModelText);
  });

//  $("#timeframe-pills a").on('click', function (event) {
//    $(this).parent().toggleClass('open');
//    $(this).parent().parent().find(".active").removeClass("active");
//    plotTimeframe = $(this).data("value");
//    plotTimeframeText = $(this).data("text");
//    replaceImageAndText(plotStnPair, plotModel, plotTimeframe, plotStnPairText, plotModelText, plotTimeframeText);
//  });

});
