(function () {
  async function gate() {
    // Don't gate the activation page itself.
    if (location.pathname.endsWith('/activate.html')) return;
    try {
      const resp = await fetch('/v1/license/status', { cache: 'no-store' });
      const st = await resp.json();
      if (!st.active) {
        // Preserve the intended destination so we can return after activation.
        const next = encodeURIComponent(location.pathname + location.search + location.hash);
        location.replace('/ui/activate.html?next=' + next);
      }
    } catch (e) {
      // If status can't be checked, fail closed: send to activation page.
      const next = encodeURIComponent(location.pathname + location.search + location.hash);
      location.replace('/ui/activate.html?next=' + next);
    }
  }

  // Run ASAP
  gate();
})();
