$(function() {


//var results = $.csv.toObjects("../top_events/slp_diff_KWMC-KSAC.csv");
//var results = $.csv.toArrays("../top_events/slp_diff_KWMC-KSAC.csv");

//config = {header:true}
//var results = Papa.parse("../top_events/slp_diff_KWMC-KSAC.csv", header=True);
//var results = Papa.parse("../top_events/slp_diff_KWMC-KSAC.csv", config);
//var results = Papa.parse("../top_events/temp1.csv");
//console.log(results);

  $("#stationMapToggle").click(function(){
        $("img").toggle(50);
    });

  $('.dropdown-menu a').on('click', function(){    
    $(this).parent().parent().prev().html($(this).html()+'<span class="caret"></span>');    
  })

//del_slp_all_init_KWMC-KSAC_gfs_10.png  
//del_slp_all_init_KWMC-KSAC_gfs_4.png   

//del_slp_all_init_KWMC-KSAC_nam_10.png   
//del_slp_all_init_KWMC-KSAC_nam_4.png
//del_slp_all_init_KWMC-KSAC_hrrr_10.png  
//del_slp_all_init_KWMC-KSAC_hrrr_4.png   

//del_slp_all_model_KWMC-KSAC_current_10.png
//del_slp_all_model_KWMC-KSAC_current_4.png

//  function createPlotName(plotStnPair, plotModel, plotTimeframe) {
//    var plotName = "del_slp_all_init_"+plotStnPair+"_"+plotModel+"_"+plotTimeframe+".png"
//    console.log(plotName);
//    return (plotName);
//  }

//images/del_slp_all_init_KWMC-KSFO_gfs_10.png
//images/del_slp_all_init_KWMC-KSFO_nam_3.png   
//images/del_slp_all_init_KWMC-KSFO_hrrr_2.png  
//images/del_slp_all_model_KWMC-KSFO_current_10.png
//images/del_slp_all_model_KWMC-KSFO_current_3.png
//images/del_slp_all_model_KWMC-KSFO_current_2.png

  function createPlotName(plotStnPair, plotModel, plotTimeframe) {
    //var plotName = plotVariable+"_"+plotRegion+"_stn_day_of_vs_time_"+plotTimeframe+".png"
    //ws_foothill_region_day_of_vs_time_current.png
    if (plotModel == "all_10d") {
        var plotTimeframe = "10" // can be 2, 3 or 10 here
        var plotName = "del_slp_all_model_"+plotStnPair+"_current_"+plotTimeframe+".png"
    } else if (plotModel == "all_3d") {
        var plotTimeframe = "3" // can be 2, 3 or 10 here
        var plotName = "del_slp_all_model_"+plotStnPair+"_current_"+plotTimeframe+".png"
    } else if (plotModel == "all_2d") {
        var plotTimeframe = "2" // can be 2, 3 or 10 here
        var plotName = "del_slp_all_model_"+plotStnPair+"_current_"+plotTimeframe+".png"
    } else {
        if (plotModel == "gfs") {var plotTimeframe = "10"}
        else if (plotModel == "nam") {var plotTimeframe = "3"}
        else if (plotModel == "hrrr") {var plotTimeframe = "2"}    
        var plotName = "del_slp_all_init_"+plotStnPair+"_"+plotModel+"_"+plotTimeframe+".png"   
    }
    console.log(plotName);
    return (plotName);
  }

//del_slp_all_model_KWMC-KSFO_current_2.png
//del_slp_all_model_KWMC-KSFO_current_10.png  
//del_slp_all_model_KWMC-KSFO_current_3.png
//<li><a href="#plot_selected" data-toggle="pill" data-value="all_2d" data-text="all models">All 2d</a></li>
//<li><a href="#plot_selected" data-toggle="pill" data-value="all_3d" data-text="all models">All 3d</a></li>
//<li><a href="#plot_selected" data-toggle="pill" data-value="all_10d" data-text="all models">All 10d</a></li>

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
    var plotPlotCdfName = "del_slp_cdf_"+plotStnPair+".png"
    //console.log(plotPlotCdfName);
    return (plotPlotCdfName);
  }

  function createTableName(plotStnPair) {
    var tableName = "del_slp_top_events_"+plotStnPair+".png"
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
    // note csmith: uncomment after 10/01
    //$("#plot_cdf").find('img').attr("src", "../top_events/"+plotCdfName);
    //$("#plot_table").find('img').attr("src", "../top_events/"+tableName);
  }

  var plotStnPair = "KWMC-KSAC";
  var plotModel = "gfs";
  var plotTimeframe = "10";

  var plotStnPairText = "Winnemucca - Sacramento";
  var plotModelText = "GFS";
  var plotTimeframeText = "10 days";
     
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
