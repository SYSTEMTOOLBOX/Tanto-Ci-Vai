from pathlib import Path

p = Path('index.html')
s = p.read_text(encoding='utf-8')

head_marker = '<meta name="theme-color" content="#0b66ff">'
head_add = '''<meta name="theme-color" content="#0b66ff">
<link rel="manifest" href="manifest.webmanifest?v=1">
<link rel="apple-touch-icon" href="assets/tcv-splash-logo.jpg?v=1">
<meta name="application-name" content="Tanto ci vai?">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="apple-mobile-web-app-title" content="Tanto ci vai?">'''

if 'rel="manifest"' not in s:
    if head_marker not in s:
        raise SystemExit('theme-color anchor not found')
    s = s.replace(head_marker, head_add, 1)

sw_marker = 'TCV_PWA_SHELL_V1'
if sw_marker not in s:
    registration = '''
<script>
/* TCV_PWA_SHELL_V1 */
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('./sw.js?v=1', { scope: './' }).catch(err => console.warn('SW registration failed', err));
  });
}
</script>
'''
    if '</body>' not in s:
        raise SystemExit('body close not found')
    s = s.replace('</body>', registration + '\n</body>', 1)

p.write_text(s, encoding='utf-8')
print('PWA shell applied')
