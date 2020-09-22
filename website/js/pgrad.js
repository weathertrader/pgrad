$(function() {

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


  function createPlotName(plotRegion,plotVariable,plotTimeframe) {
    //var plotName = plotVariable+"_"+plotRegion+"_stn_day_of_vs_time_"+plotTimeframe+".png"
    //ws_foothill_region_day_of_vs_time_current.png
    var plotName = plotVariable+"_"+plotRegion+"_region_day_of_vs_time_"+plotTimeframe+".png"
    console.log(plotName);
    return (plotName);
  }

  function createPlotText(plotRegionText,plotVariableText,plotTimeframeText) {
    //var plotText = "Forecast "+plotVariableText+" at "+plotRegionText+" for "+plotTimeframeText
    var plotText = "Forecast "+plotVariableText+" at "+plotRegionText+" stations for "+plotTimeframeText
    console.log(plotText);
    return (plotText);
  }

  function replaceImageAndText(plotRegion,plotRegionText,plotVariable,plotVariableText,plotTimeframe,plotTimeframeText) {
    plotName = createPlotName(plotRegion,plotVariable,plotTimeframe);
    plotText = createPlotText(plotRegionText,plotVariableText,plotTimeframeText);
    $("#plot_selected").find('img').attr("src", "images/"+plotName);
    //$("#plot_selected_text").text(plotText);
    $("#plot_text").text(plotText);
  }

  var plotRegion = "foothill";
  var plotVariable = "ws";
  var plotTimeframe = "current";

  var plotRegionText = "foothill";
  var plotVariableText = "wind speed";
  var plotTimeframeText = "today";
     
  plotName = createPlotName(plotRegion,plotVariable,plotTimeframe);
  plotText = createPlotText(plotRegionText,plotVariableText,plotTimeframe);

  $("#variable-pills a").on('click', function (event) {
    $(this).parent().toggleClass('open');
    $(this).parent().parent().find(".active").removeClass("active");
    plotVariable     = $(this).data("variable");
    plotVariableText = $(this).data("text");
    replaceImageAndText(plotRegion,plotRegionText,plotVariable,plotVariableText,plotTimeframe,plotTimeframeText);
  });

  $("#region-pills a").on('click', function (event) {
    $(this).parent().toggleClass('open');
    $(this).parent().parent().find(".active").removeClass("active");
    plotRegion = $(this).data("region");
    plotRegionText = $(this).data("text");
    replaceImageAndText(plotRegion,plotRegionText,plotVariable,plotVariableText,plotTimeframe,plotTimeframeText);
  });

  $("#timeframe-pills a").on('click', function (event) {
    $(this).parent().toggleClass('open');
    $(this).parent().parent().find(".active").removeClass("active");
    plotTimeframe = $(this).data("timeframe");
    plotTimeframeText = $(this).data("text");
    replaceImageAndText(plotRegion,plotRegionText,plotVariable,plotVariableText,plotTimeframe,plotTimeframeText);
  });

});
