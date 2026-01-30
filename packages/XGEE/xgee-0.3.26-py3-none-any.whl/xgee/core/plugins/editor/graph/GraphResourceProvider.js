/* GRAPH RESOURCE PROVIDER */

function GraphResourceProvider(basePath) {
  this.basePath = basePath;

  this.resourceCache = new Map(); // do not load a resource twice
  this.URLCache = new Map();

  return this;
}

GraphResourceProvider.prototype.LoadResource = function (path) {
  var realPath = this.basePath + path;
  if (this.resourceCache.has(realPath)) {
    return this.resourceCache.get(realPath);
  }
  var resource = this.__LoadResourceExternaly(realPath);
  this.resourceCache.set(realPath, resource);
  return resource;
};

GraphResourceProvider.prototype.__LoadResourceExternaly = function (path) {
  var xhttp = new XMLHttpRequest();
  xhttp.open("GET", path, false);
  try {
    xhttp.send();
    let responseText = xhttp.responseText || "";
    let requestError = xhttp.status === 0 && responseText.length === 0;
    let cannotLoad = xhttp.status >= 400;
    if (requestError || cannotLoad) {
      console.warn(
          "Could not load resource (Status " + xhttp.status + "): " + path + ". Using fallback SVG 'Missing'.",
      );
      return '<svg width="100" height="100" xmlns="http://www.w3.org/2000/svg"><rect width="100%" height="100%" fill="#ffcccc" stroke="red" stroke-width="2"/><text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" fill="red" font-size="12">Missing</text></svg>';
    }
  } catch (err) {
    console.warn("Unexpected error. Could not load resource: " + path, err);
    throw new Error("Unexpected error. Could not load resource: " + path);
  }
  return xhttp.responseText;
};

GraphResourceProvider.prototype.LoadResourceToBlobURL = function (path) {
  var realPath = this.basePath + path;
  if (this.URLCache.has(realPath)) {
    return this.URLCache.get(realPath);
  }
  var resource = this.__LoadResourceExternaly(realPath);
  let blob = new Blob([resource], { type: "image/svg+xml" });
  let url = URL.createObjectURL(blob);
  this.URLCache.set(realPath, url);
  return url;
};

export default GraphResourceProvider;
