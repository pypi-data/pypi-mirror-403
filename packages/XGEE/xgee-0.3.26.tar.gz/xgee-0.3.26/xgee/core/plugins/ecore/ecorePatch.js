// Patch for Ecore.js to handle automatic type conversion for EBoolean
// was "true", with this wrapper: true
// This complements the default value fix in @xgee-launcher-package/xgee/core/plugins/editor/plugin.js (_fixDefaultsEClass)

export default function applyEcorePatch(Ecore) {
  if (!Ecore || !Ecore.EClass) {
    console.warn("Ecore patch failed: Ecore or Ecore.EClass not found.");
    return;
  }

  // EObject constructor is hidden in the library closure.
  // We must retrieve the prototype from an existing instance.
  // Ecore.EClass is a static instance of EObject exposed by the library.
  const EObjectProto = Object.getPrototypeOf(Ecore.EClass);

  if (!EObjectProto || typeof EObjectProto.set !== "function") {
    console.warn("Ecore patch failed: Could not retrieve EObject prototype or set method.");
    return;
  }

  const originalSet = EObjectProto.set;

  EObjectProto.set = function (attrs, options) {
    // Helper to get feature by name (similar to internal getEStructuralFeature)
    const getFeature = (eClass, featureName) => {
      let allFeatures = eClass.get("eAllStructuralFeatures");

      // Handle EList by converting to array
      if (allFeatures && typeof allFeatures.array === "function") {
        allFeatures = allFeatures.array();
      }

      if (!Array.isArray(allFeatures)) return null;

      for (let i = 0; i < allFeatures.length; i++) {
        if (allFeatures[i].get("name") === featureName) {
          return allFeatures[i];
        }
      }
      return null;
    };

    if (attrs && typeof attrs === "object" && !attrs.eClass) {
      // Case 1: attrs is a dictionary of { feature: value }
      // untested, unlikely case
      for (const featureName in attrs) {
        if (Object.prototype.hasOwnProperty.call(attrs, featureName)) {
          const feature = getFeature(this.eClass, featureName);
          if (feature) {
            const eType = feature.get("eType");
            if (eType && (eType.get("name") === "EBoolean" || eType.get("name") === "EBooleanObject")) {
              const val = attrs[featureName];
              if (typeof val === "string") {
                attrs[featureName] = val.trim().toLowerCase() === "true";
              }
            }
          }
        }
      }
    } else {
      // Case 2: set(name, value) OR set(feature, value)
      let featureName;
      let val = options;

      if (attrs && typeof attrs === "object" && attrs.eClass) {
          // Argument is an EStructuralFeature
          featureName = attrs.get("name");
      } else if (typeof attrs === "string") {
          // Argument is a string name
          // usual case
          featureName = attrs;
      }

      if (featureName) {
        const feature = getFeature(this.eClass, featureName);
        if (feature) {
          const eType = feature.get("eType");
          if (eType && (eType.get("name") === "EBoolean" || eType.get("name") === "EBooleanObject")) {
            if (typeof val === "string") {
              val = val.trim().toLowerCase() === "true";
              // Update the value argument for the original call
              options = val;
            }
          }
        }
      }
    }

    return originalSet.call(this, attrs, options);
  };

  console.debug("Ecore.js patched: EBoolean set() type conversion enabled via prototype injection.");
}