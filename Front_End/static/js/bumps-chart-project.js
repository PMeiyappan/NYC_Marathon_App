

$(document).ready(function(){
  (function e(t, n, r) {
      function s(o, u) {
          if (!n[o]) {
              if (!t[o]) {
                  var a = typeof require == "function" && require;
                  if (!u && a) return a(o, !0);
                  if (i) return i(o, !0);
                  throw new Error("Cannot find module '" + o + "'")
              }
              var f = n[o] = {
                  exports: {}
              };
              t[o][0].call(f.exports, function(e) {
                  var n = t[o][1][e];
                  return s(n ? n : e)
              }, f, f.exports, e, t, n, r)
          }
          return n[o].exports
      }
      var i = typeof require == "function" && require;
      for (var o = 0; o < r.length; o++) s(r[o]);
      return s
  })({
      1: [function(require, module, exports) {
          var render = require("./modules/render"),
              config = require("../project-config.json");
          render.renderViz(config)
      }, {
          "../project-config.json": 8,
          "./modules/render": 7
      }],
      2: [function(require, module, exports) {
          var misc = require("./misc"),
              mouse = require("./mouse");
          module.exports.assemble = function(params, data, vizType) {
              var ds = misc.dataStructs(data),
                  scales = misc.genScales(params, ds.splits),
                  sel = objs(params, ds, scales);
              misc.skeleton(vizType, params.spacer, scales, sel.splitLines);
              animate();
              var cnt = 0,
                  l = data.length;

              function postMouse() {
                  cnt += 1;
                  if (cnt === l) {
                      sel.clearPath.on("mouseenter", function(el) {
                          mouse.mouseEnter(sel, params, ds.meta, el, "line", vizType)
                      }).on("mousemove", function(el) {
                          mouse.mouseEnter(sel, params, ds.meta, el, "line", vizType)
                      }).on("mouseleave", function(el) {
                          mouse.mouseLeave(sel, params)
                      });
                      sel.marker.on("mouseenter", function(el) {
                          mouse.mouseEnter(sel, params, ds.meta, el, "marker", vizType)
                      }).on("mousemove", function(el) {
                          mouse.mouseEnter(sel, params, ds.meta, el, "marker", vizType)
                      }).on("mouseleave", function(el) {
                          mouse.mouseLeave(sel, params)
                      })
                  }
              }

              function dur(d, i) {
                  var tot_time = d.slice(-1)[0].split_mins;
                  var scaled = Math.pow(tot_time, 2) * .25;
                  return scaled
              }

              function translateAlong(path) {
                  var l = path.getTotalLength();
                  return function(i) {
                      return function(t) {
                          var p = path.getPointAtLength(t * l);
                          return "translate(" + p.x + "," + p.y + ")"
                      }
                  }
              }

              function transitionThis(d, i) {
                  d3.select(this).transition().duration(function(d, i) {
                      return dur(d, i)
                  }).ease("quad").attrTween("transform", translateAlong(sel.strokes[i]))
              }

              function animate() {
                  sel.path.each(function(d) {
                      d.totalLength = this.getTotalLength()
                  }).attr("stroke-dasharray", function(d) {
                      return d.totalLength + " " + d.totalLength
                  }).attr("stroke-dashoffset", function(d) {
                      return d.totalLength
                  }).transition().duration(function(d, i) {
                      return dur(d, i)
                  }).ease("quad").attr("stroke-dashoffset", 0).each("end", postMouse);
                  sel.marker.each(transitionThis);
                  sel.markerText.each(transitionThis)
              }
          };
          var objs = function(params, ds, scales) {
              var line = d3.svg.line().x(function(d, i) {
                  return scales.xs(d.split_dist)
              }).y(function(d, i) {
                  return scales.ys(d.split_place)
              });
              var nodeGroup = params.svg.append("g").attr("transform", "translate(" + params.margin.left + "," + params.margin.top + ")");
              var splitLines = nodeGroup.selectAll("line").data(ds.splitStrs).enter();
              var splitNodes = nodeGroup.selectAll("polygon").data(ds.splits).enter();
              var tooltip = d3.select(params.sel).append("div").attr("class", "tooltips hidden");
              var mc = misc.markerCof(params);
              var marker = splitNodes.append("polygon").attr("points", misc.lineMarker(params.height * .0088, params.width * .025)).attr("fill", function(d, i) {
                  return scales.cs(d[0].year)
              });
              var markerText = splitNodes.append("text").attr("dx", "1.5em").attr("dy", "0.35em").style("font-size", params.spacer).text(function(d, i) {
                  var rank = d.slice(-1)[0].split_place + 1;
                  return misc.placeString(rank).split(" ")[0]
              }).style("opacity", 0);
              var path = splitNodes.append("path").attr("class", "path").attr("stroke", function(d, i) {
                  return scales.cs(d[0].year)
              }).attr("fill", "none").attr("stroke-width", params.spacer / 3).attr("id", function(d, i) {
                  return "path_" + i
              }).attr("stroke-linecap", "round").attr("d", function(d) {
                  return line(d)
              });
              var clearPath = splitNodes.append("path").attr("class", function(d) {
                  return "path_" + d[0].runner_idx
              }).attr("stroke", "black").attr("fill", "none").attr("stroke-width", params.spacer).attr("stroke-linecap", "round").attr("d", function(d) {
                  return line(d)
              }).style("opacity", 0);
              var strokes = ds.splits.map(function(d, i) {
                  return params.svg.select("#path_" + i).node()
              });
              return {
                  marker: marker,
                  markerText: markerText,
                  path: path,
                  clearPath: clearPath,
                  splitLines: splitLines,
                  strokes: strokes,
                  tooltip: tooltip
              }
          }
      }, {
          "./misc": 5,
          "./mouse": 6
      }],
      3: [function(require, module, exports) {
          var misc = require("./misc");
          module.exports.params = function(sel, fn) {
              var colors = {
                  gray: "#999999",
                  green: "#8CC63E",
                  orange: "#F7941D",
                  blue: "#00ADEF",
                  purple: "#652D90",
                  magenta: "#ED008B"
              };
              var aspect = 1.4,
                  W = parseFloat(d3.select(sel).style("width")),
                  H = W / aspect,
                  spacer = misc.space(H, W, .03);
              var margin = {
                      top: spacer,
                      bottom: spacer,
                      left: spacer,
                      right: spacer * 2
                  },
                  width = W - margin.left - margin.right,
                  height = H - margin.top - margin.bottom;
              var viewBox = "0 0 " + W + " " + H;
              var svg = d3.select(sel).append("svg").attr("viewBox", viewBox).attr("width", width + margin.left + margin.right).attr("height", height + margin.top + margin.bottom).append("g").attr("transform", "translate(" + margin.left + "," + margin.top + ")");
              var p = {
                  sel: sel,
                  svg: svg,
                  height: height,
                  width: width,
                  margin: margin,
                  spacer: spacer,
                  colors: colors
              };
              fn(p)
          }
      }, {
          "./misc": 5
      }],
      4: [function(require, module, exports) {
          var misc = require("./misc");
          module.exports.params = function(sel, fn) {
              var colors = {
                  gray: "#999999",
                  green: "#8CC63E",
                  orange: "#F7941D",
                  blue: "#00ADEF",
                  purple: "#652D90",
                  magenta: "#ED008B"
              };
              var aspect = 1.9,
                  sW = parseFloat(d3.select(sel).style("width")) * .9,
                  W = sW > 500 ? 500 : sW,
                  H = $(window).height() * .9 / 2,
                  spacer = misc.space(H, W, .03);
              var margin = {
                      top: spacer,
                      bottom: spacer,
                      left: spacer,
                      right: spacer * 3
                  },
                  width = W - margin.left - margin.right,
                  height = H - margin.top - margin.bottom;
              var viewBox = "0 0 " + W + " " + H;
              var svg = d3.select(sel).append("svg").attr("viewBox", viewBox).attr("width", width + margin.left + margin.right).attr("height", height + margin.top + margin.bottom).append("g").attr("transform", "translate(" + margin.left + "," + margin.top + ")");
              var p = {
                  sel: sel,
                  svg: svg,
                  height: height,
                  width: width,
                  margin: margin,
                  spacer: spacer,
                  colors: colors
              };
              fn(p)
          }
      }, {
          "./misc": 5
      }],
      5: [function(require, module, exports) {
          module.exports.space = function space(hspacer, wspacer, perc) {
              return hspacer < wspacer ? hspacer * perc : wspacer * perc
          };
          module.exports.placeString = function(place) {
              var skipInts = {
                      11: undefined,
                      12: undefined,
                      13: undefined
                  },
                  suffixMap = {
                      1: "st",
                      2: "nd",
                      3: "rd"
                  },
                  lstDigit = place % 10;
              if (lstDigit in suffixMap && !(place in skipInts)) {
                  var pl = place + suffixMap[lstDigit]
              } else {
                  var pl = place + "th"
              }
              return pl + " place"
          };
          module.exports.lineMarker = function(h, k) {
              var a = k,
                  b = k,
                  point = a + h;
              var poly = [a, ",-", h, " ", b, ",-", h, " 0,-", h, , " 0,", h, , " ", b, ",", h, " ", a, ",", h, " ", point, ",0 "].join("");
              return poly
          };
          module.exports.markerCof = function(params) {
              var offwidth = 20,
                  ch = params.height * .025 / 4,
                  cw = params.width * .0088 * 4 > offwidth ? params.width * .0088 * 4 : offwidth;
              return {
                  ch: ch,
                  cw: cw
              }
          };
          module.exports.skeleton = function(vizType, spacer, scales, splitLines) {
              var mxRunners = scales.ys.domain()[1];
              splitLines.append("line").attr("x1", function(d, i) {
                  return scales.xs(d.split_dist)
              }).attr("y1", scales.ys(0) - spacer).attr("x2", function(d, i) {
                  return scales.xs(d.split_dist)
              }).attr("y2", scales.ys(mxRunners) + spacer).attr("stroke", "#999999").attr("stroke-width", 1.5).style("opacity", .5);
              splitLines.append("text").attr("class", "split-text").filter(function(d) {
                  return d.split_label !== "Pre-Finish"
              }).attr("x", function(d, i) {
                  return scales.xs(d.split_dist)
              }).attr("y", scales.ys(0) - spacer).attr("dy", "-0.35em").style("text-anchor", function(d) {
                  if (d.split_label === "Half" || d.split_label === "Finish") {
                      return "start"
                  } else {
                      return "middle"
                  }
              }).style("font-size", vizType === "project" ? spacer + "px" : spacer * 1.3 + "px").text(function(d) {
                  return d.split_label
              })
          };
          var metaMap = function(data) {
              var map = data.reduce(function(acc, el) {
                  var idx = el.splits[0].runner_idx;
                  var year = el.splits[0].year;
                  var datum = {
                      name: el.name,
                      country: el.co,
                      place: el.place,
                      year: year,
                      offlTime: el.offl_time
                  };
                  acc[idx] = datum;
                  return acc
              }, {});
              return map
          };
          module.exports.dataStructs = function(data) {
              var splits = _.pluck(data, "splits");
              var splitStrs = splits.sort(function(a, b) {
                  return b.length - a.length
              }).slice(0, 1)[0];
              var meta = metaMap(data);
              return {
                  splits: splits,
                  splitStrs: splitStrs,
                  meta: meta
              }
          };
          module.exports.genScales = function(it, splits) {
              var margin = it.margin,
                  width = it.width,
                  height = it.height;
              var mxRunners = splits.length;
              var mxSplitN = d3.max(splits, function(d) {
                  return d.length
              });
              var yearExt = d3.extent(splits.map(function(d) {
                  return d[0].year
              }));
              var distExt = splits.reduce(function(acc, el) {
                  var elemMn = el[0].split_dist,
                      elemMx = el.slice(-1)[0].split_dist;
                  if (elemMn < acc.mnDist) {
                      acc.mnDist = elemMn
                  }
                  if (elemMx > acc.mxDist) {
                      acc.mxDist = elemMx
                  }
                  return acc
              }, {
                  mnDist: Infinity,
                  mxDist: -Infinity
              });
              var xScale = d3.scale.linear().domain([distExt.mnDist, distExt.mxDist]).range([0, width - margin.right - margin.left]);
              var yScale = d3.scale.linear().domain([0, mxRunners]).range([margin.top, height - margin.bottom]);
              var colorScale = d3.scale.ordinal().domain(yearExt).range(["#F7941D", "#00ADEF", "#652D90", "#8CC63E", "#ED008B"]);
              return {
                  xs: xScale,
                  ys: yScale,
                  cs: colorScale
              }
          }
      }, {}],
      6: [function(require, module, exports) {
          var misc = require("./misc");
          var selTextAbbr = function(hoverElems) {
              var nameParts = hoverElems.name.trim().split(" ");
              var fstNameAbbr = nameParts[0][0] + ".",
                  lastName = nameParts.slice(-1)[0],
                  fullName = [fstNameAbbr, " ", lastName].join(""),
                  coAbbr = [" (", hoverElems.country, ")"].join(""),
                  finish = "Finish: " + hoverElems.offlTime;
              var label = hoverElems.type === "marker" ? fullName : fullName + coAbbr;
              var html = [label, finish, hoverElems.rank].join("<br>");
              return html
          };
          module.exports.mouseEnter = function(sel, params, meta, el, type, vizType) {
              var duration = 250,
                  opacity = .05,
                  mouse = d3.mouse(params.svg.node()).map(function(d) {
                      return parseInt(d)
                  }),
                  key = el[0].runner_idx,
                  metaDatum = meta[key];
              var rank = [misc.placeString(metaDatum.place), ", ", metaDatum.year].join("");
              sel.marker.filter(function(d) {
                  return key !== d[0].runner_idx
              }).transition().duration(duration).style("opacity", opacity);
              sel.markerText.filter(function(d) {
                  return key === d[0].runner_idx
              }).transition().duration(duration).style("opacity", 1);
              sel.path.filter(function(d) {
                  return key !== d[0].runner_idx
              }).transition().duration(duration).style("opacity", opacity);
              var hoverElems = {
                  name: metaDatum.name,
                  country: metaDatum.country,
                  rank: rank,
                  offlTime: metaDatum.offlTime,
                  type: type
              };
              var html = selTextAbbr(hoverElems);
              var rProps = {
                  x: -params.width / 38,
                  y: -params.width / 9.5,
                  f: params.width / 60
              };
              if (vizType === "project") {
                  var c = 2;
                  rProps = {
                      x: rProps.x * c,
                      y: rProps.y * c,
                      f: rProps.f * c
                  }
              }
              sel.tooltip.classed("hidden", false).style("left", d3.event.pageX + rProps.x + "px").style("top", d3.event.pageY + rProps.y + "px").style("font-size", rProps.f + "px").html(html)
          };
          module.exports.mouseLeave = function(sel, params) {
              sel.tooltip.classed("hidden", true);
              var duration = 250;
              sel.marker.transition().duration(duration).style("opacity", 1);
              sel.markerText.transition().duration(duration).style("opacity", 0);
              sel.path.transition().duration(duration).style("opacity", 1);
              params.svg.selectAll(".split-text").transition().duration(duration).ease("linear").style("opacity", 1)
          }
      }, {
          "./misc": 5
      }],
      7: [function(require, module, exports) {
          var initpst = require("./init-post"),
              initprj = require("./init-project"),
              assemble = require("./assemble");
          var go = function(config, vizElem, data) {
              if (config.type === "post") {
                  initpst.params(vizElem, function(it) {
                      assemble.assemble(it, data, config.type)
                  })
              }
              if (config.type === "project") {
                  initprj.params(vizElem, function(it) {
                      assemble.assemble(it, data, config.type)
                  })
              }
          };
          var loadJson = function(jsonFile, fn) {
              d3.json(jsonFile, function(err, data) {
                  fn(data)
              })
          };
          var renderEach = function(vizElems, fn) {
              vizElems.forEach(function(d) {
                  d3.select(d.elem).selectAll("svg").remove();
                  fn(d.elem, d.data)
              })
          };
          var renderAll = function(config) {
              renderEach(config.data, function(elem, jsonFile) {
                  loadJson(jsonFile, function(json) {
                      go(config, elem, json)
                  })
              })
          };
          var renderViz = function(config) {
              renderAll(config);
              $(window).on("resize", function() {
                  d3.selectAll("svg").selectAll(".tooltips").remove();
                  renderAll(config)
              });
              if (config.type === "post") {
                  config.data.forEach(function(d) {
                      d3.select(d.button).on("click", function() {
                          renderAll({
                              type: "post",
                              data: [d]
                          })
                      })
                  })
              } else if (config.type === "project") {
                  d3.select(config.data[0].button).on("click", function() {
                      renderAll(config)
                  })
              }
          };
          module.exports.renderViz = renderViz
      }, {
          "./assemble": 2,
          "./init-post": 3,
          "./init-project": 4
      }],
      8: [function(require, module, exports) {
          module.exports = {
              type: "project",
              multiple: 1.7,
              data: [ {
                  data: $('#chart').data('url'),
                  elem: "#chart",
                  button: ".btn"
              }]
          }
      }, {}]
  }, {}, [1]);


});