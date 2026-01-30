window.MathJax = {
  tex: {
    inlineMath: [["\\(", "\\)"]],
    displayMath: [["\\[", "\\]"]],
    processEscapes: true,
    processEnvironments: true
  },
  options: {
    ignoreHtmlClass: ".*|",
    processHtmlClass: "arithmatex"
  },
  loader: {
    load: ['[tex]/mathtools', '[tex]/physics']
  },
  startup: {
    ready: function() {
      console.log('MathJax loaded successfully');
      MathJax.startup.defaultReady();
    }
  }
};