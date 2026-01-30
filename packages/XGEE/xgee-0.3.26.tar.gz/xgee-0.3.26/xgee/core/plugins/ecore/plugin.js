import applyEcorePatch from "./ecorePatch.js";

export function init(pluginAPI) {
  return pluginAPI
    .loadScripts(["sax-js-master/lib/sax.js", "ecore.xmi.js"])
    .then(function () {
      const Ecore = window["Ecore"];
      
      // Apply runtime patch for EBoolean set() conversion
      // See also default value fix in @xgee-launcher-package/xgee/core/plugins/editor/plugin.js
      applyEcorePatch(Ecore);

      pluginAPI.expose({ Ecore: Ecore });
      return Promise.resolve();
    });
}

export var meta = {
  id: "ecore",
  description: "ecore javascript implementation",
  author: "Guillaume Hillairet, Isaac Z. Schlueter et al.",
  version: "0.0.0",
  requires: [],
};
