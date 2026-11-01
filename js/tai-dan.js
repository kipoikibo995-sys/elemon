// Elemon: the demo's pictures loaded screen by screen (before the demo's own script, which calls __lazyJobs where it
// started all ~1100 loads at once). At start only the pictures every screen may need (the room, the menus, food,
// decor, eggs...); each screen's own set (the farm, fishing, cooking, school, the shop, the bag, the bath, the
// stats pages, the hatching) is read when that screen opens (game/src/tai-man.js, a short loading screen)
// or bit by bit in the background before that. The game grows by screens; its start does not have to.
(() => {
  // screen -> the picture names only it uses (backdrops, "nen", stay common: the activity menu shows them)
  // (only pictures no other screen draws: the item icons in the bag and the shop - crops, fish, dishes -, the
  // teacher's faces the cooking result uses too, the popup frame, the backdrops, the shop's backdrop stay common)
  const GROUPS = {
    farm: n => /^fm_/.test(n) && !/nen|_5-nong-san$/.test(n),
    fish: n => /^cc_/.test(n) && !/nen|^cc_CA_|^cc_ca_icon$/.test(n),
    cook: n => /^na_(cat|khuay|chien|xong)_dai6$|^na_(mui-ten-xuong|xoay|kim-chi|truot|hoan-hao)$|^na_(vong|thanh)_/.test(n),
    school: n => /^th_/.test(n) && !/nen|^th_co_/.test(n),
    shop: n => (/^shop_/.test(n) && n !== 'shop_bg') || n === 'chu-quan' || n === 'nhan-gia',
    tui: n => /^td_/.test(n) && n !== 'td_tui',
    bath: n => /^tam_/.test(n),
    stats: n => /^stats_/.test(n),
    hatch: n => /^no_(hoa|kim|moc|thuy|tho)_/.test(n),
  };
  globalThis.__LAZY = { groups: {}, load: null, done: {}, started: {} };
  // the pet the demo reads at start: the one played last (its "Tiếp tục" then has it already), not always Hỏa Hổ
  globalThis.__startPet = () => {
    try { const t = localStorage.getItem(localStorage.getItem('holua-cuoi') || 'holua-save-1'), sv = t && JSON.parse(t); return sv && sv.pet && sv.pet.creature; }
    catch (e) { return null; }
  };
  globalThis.__lazyJobs = (files, load) => {
    const L = globalThis.__LAZY, now = [];
    L.load = load;
    for (const f of files) {
      const g = Object.keys(GROUPS).find(k => GROUPS[k](f));
      if (g) (L.groups[g] = L.groups[g] || []).push(f); else now.push(f);
    }
    return now.map(f => load(f, `img/${f}.png`));
  };
})();
