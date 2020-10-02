$(function() {

  $("#stationMapToggle").click(function(){
        $("img").toggle(50);
    });

  $('.dropdown-menu a').on('click', function(){    
    $(this).parent().parent().prev().html($(this).html()+'<span class="caret"></span>');    
  })

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
