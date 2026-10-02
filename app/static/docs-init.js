"use strict";
window.addEventListener("DOMContentLoaded", function () {
  const root = document.getElementById("swagger-ui");
  window.ui = SwaggerUIBundle({
    url: root.dataset.openapiUrl,
    dom_id: "#swagger-ui",
    deepLinking: true,
    presets: [SwaggerUIBundle.presets.apis],
    layout: "BaseLayout",
    persistAuthorization: false,
    validatorUrl: null
  });
});
