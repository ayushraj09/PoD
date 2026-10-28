(function () {
  var s = document.currentScript || document.querySelector('script[data-waitlist]');
  if (!s) return;
  var slug = s.getAttribute('data-waitlist');
  var origin = new URL(s.src).origin;
  var f = document.createElement('iframe');
  f.src = origin + '/w/' + encodeURIComponent(slug);
  f.allow = 'microphone';
  f.title = 'Join the waitlist';
  f.style.cssText = 'width:100%;max-width:480px;height:' + (s.getAttribute('data-height') || '520') + 'px;border:0;';
  s.parentNode.insertBefore(f, s.nextSibling);
})();
