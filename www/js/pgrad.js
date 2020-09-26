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

//  function createPlotName(plotStn1, plotStn2, plotModel, plotTimeframe) {
//    var plotName = "del_slp_all_init_"+plotStn1+"-"+plotStn2+"_"+plotModel+"_"+plotTimeframe+".png"
//    console.log(plotName);
//    return (plotName);
//  }

//images/del_slp_all_init_KWMC-KSFO_gfs_10.png
//images/del_slp_all_init_KWMC-KSFO_nam_3.png   
//images/del_slp_all_init_KWMC-KSFO_hrrr_2.png  
//images/del_slp_all_model_KWMC-KSFO_current_10.png
//images/del_slp_all_model_KWMC-KSFO_current_3.png
//images/del_slp_all_model_KWMC-KSFO_current_2.png

  function createPlotName(plotStn1, plotStn2, plotModel, plotTimeframe) {
    //var plotName = plotVariable+"_"+plotRegion+"_stn_day_of_vs_time_"+plotTimeframe+".png"
    //ws_foothill_region_day_of_vs_time_current.png
    if (plotModel == "all_model") {
        var plotTimeframe = "10" // can be 2, 3 or 10 here
        var plotName = "del_slp_all_model_"+plotStn1+"-"+plotStn2+"_current_"+plotTimeframe+".png"
    } else {
        if (plotModel == "gfs") {var plotTimeframe = "10"}
        else if (plotModel == "nam") {var plotTimeframe = "3"}
        else if (plotModel == "hrrr") {var plotTimeframe = "2"}    
        var plotName = "del_slp_all_init_"+plotStn1+"-"+plotStn2+"_"+plotModel+"_"+plotTimeframe+".png"   
    }
    console.log(plotName);
    return (plotName);
  }

  function createPlotText(plotStn1Text, plotStn2Text, plotModelText) {
    //var plotText = "Forecast "+plotVariableText+" at "+plotRegionText+" for "+plotTimeframeText
    if (plotModel == "all_model") {
        var plotText = "Forecast pressure difference, "+plotStn1Text+" - "+plotStn2Text+", all models most recent init"
    } else {
        var plotText = "Forecast pressure difference, "+plotStn1Text+" - "+plotStn2Text+", "+plotModelText+" all init"
    }
    console.log(plotText);
    return (plotText);
  }

  function createPlotCdfName(plotStn1, plotStn2) {
    var plotPlotCdfName = "del_slp_cdf_"+plotStn1+"-"+plotStn2+".png"
    console.log(plotPlotCdfName);
    return (plotPlotCdfName);
  }

  function createTableName(plotStn1, plotStn2) {
    var tableName = "del_slp_top_events_"+plotStn1+"-"+plotStn2+".png"
    console.log(tableName);
    return (tableName);
  }

  function replaceImageAndText(plotStn1, plotStn2, plotModel, plotStn1Text, plotStn2Text, plotModelText) {
    plotText    = createPlotText(plotStn1Text, plotStn2Text, plotModelText);
    plotName    = createPlotName(plotStn1, plotStn2, plotModel);
    plotCdfName = createPlotCdfName(plotStn1, plotStn2);
    tableName   = createTableName(plotStn1, plotStn2);    
    $("#plot_text").text(plotText);
    $("#plot_selected").find('img').attr("src", "../../images/"+plotName);
    $("#plot_cdf").find('img').attr("src", "../../top_events/"+plotCdfName);
    $("#plot_table").find('img').attr("src", "../../top_events/"+tableName);
//    $("#plot_selected").find('img').attr("src", "../../images/"+plotName);
//    $("#plot_cdf").find('img').attr("src", "../../top_events/"+plotCdfName);
//    $("#plot_table").find('img').attr("src", "../../top_events/"+tableName);
  }

  var plotStn1 = "KWMC";
  var plotStn2 = "KSAC";
  var plotModel = "gfs";
  var plotTimeframe = "10";

  var plotStn1Text = "Winnemucca";
  var plotStn2Text = "Sacramento";
  var plotModelText = "GFS";
  var plotTimeframeText = "10 days";
     
     
     
  plotName = createPlotName(plotStn1, plotStn2, plotModel);
  plotText = createPlotText(plotStn1Text, plotStn2Text, plotModelText);
  plotCdfName = createPlotCdfName(plotStn1, plotStn2);
  tableName   = createTableName(plotStn1, plotStn2);

  $("#stn1-pills a").on('click', function (event) {
    $(this).parent().toggleClass('open');
    $(this).parent().parent().find(".active").removeClass("active");
    plotStn1     = $(this).data("value");
    plotStn1Text = $(this).data("text");
    replaceImageAndText(plotStn1, plotStn2, plotModel, plotStn1Text, plotStn2Text, plotModelText);
  });

  $("#stn2-pills a").on('click', function (event) {
    $(this).parent().toggleClass('open');
    $(this).parent().parent().find(".active").removeClass("active");
    plotStn2     = $(this).data("value");
    plotStn2Text = $(this).data("text");
    replaceImageAndText(plotStn1, plotStn2, plotModel, plotStn1Text, plotStn2Text, plotModelText);
  });

  $("#model-pills a").on('click', function (event) {
    $(this).parent().toggleClass('open');
    $(this).parent().parent().find(".active").removeClass("active");
    plotModel = $(this).data("value");
    plotModelText = $(this).data("text");
    replaceImageAndText(plotStn1, plotStn2, plotModel, plotStn1Text, plotStn2Text, plotModelText);
  });

//  $("#timeframe-pills a").on('click', function (event) {
//    $(this).parent().toggleClass('open');
//    $(this).parent().parent().find(".active").removeClass("active");
//    plotTimeframe = $(this).data("value");
//    plotTimeframeText = $(this).data("text");
//    replaceImageAndText(plotStn1, plotStn2, plotModel, plotTimeframe, plotStn1Text, plotStn2Text, plotModelText, plotTimeframeText);
//  });

});
