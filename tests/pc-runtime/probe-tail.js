(() => { const f0 = globalThis.__frame; globalThis.__frame = now => { f0(now); __probeFrame(now); }; })();
