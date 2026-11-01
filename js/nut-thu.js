// Test buttons beside the screen of the browser page (only there: <script data-browser-only>, the R36S package leaves
// it out). They change the game state directly, to look at things without playing hours: evolve, pick any stage or
// pet, move house, jump to a screen, set the needs, add gold, jump the clock.
// While the ~1100 pictures load (slow through the test server) the demo draws nothing: show how far it has got.
(function loading() {
  if (typeof last === 'number' && last > 0) return;              // the game loop has started
  const n = Object.keys(IMG).length, all = typeof jobs !== 'undefined' ? jobs.length : 0;
  ctx.fillStyle = '#000'; ctx.fillRect(0, 0, 640, 480);
  ctx.fillStyle = '#f0e4ce'; ctx.font = 'bold 20px Tahoma, sans-serif'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  ctx.fillText(`Đang tải hình… ${Math.min(n, all)}/${all}`, 320, 230);
  ctx.fillStyle = '#3a2618'; ctx.fillRect(170, 256, 300, 10);
  ctx.fillStyle = '#ffd36e'; ctx.fillRect(170, 256, all ? 300 * Math.min(1, n / all) : 0, 10);
  setTimeout(loading, 250);
})();
(() => {
  const side = document.querySelector('.side') || document.body;
  const box = document.createElement('div');
  box.innerHTML = `<style>
    .thu { margin-top: 14px; border-top: 1px solid #3a2f26; padding-top: 10px; }
    .thu h3 { margin: 4px 0 6px; }
    .thu .row { display: flex; flex-wrap: wrap; gap: 5px; margin: 4px 0 8px; align-items: center; }
    .thu .lb { color: #a08a6e; font-size: 12px; width: 100%; }
    .thu button, .thu select { font: bold 12px "Segoe UI", sans-serif; border-radius: 6px; border: 1px solid #8a6a3a;
      background: #3a2618; color: #f6dfb0; padding: 4px 8px; cursor: pointer; }
    .thu button:hover { background: #553822; }
    .thu .st { color: #a08a6e; font-size: 12px; margin-top: 4px; white-space: pre-line; }
  </style><div class="thu"><h3>Nút test</h3><div id="thuRows"></div><div class="st" id="thuState"></div></div>`;
  side.appendChild(box);
  const rows = box.querySelector('#thuRows'), state = box.querySelector('#thuState');
  const row = label => { const r = document.createElement('div'); r.className = 'row'; r.innerHTML = `<div class="lb">${label}</div>`; rows.appendChild(r); return r; };
  const btn = (r, text, fn) => { const b = document.createElement('button'); b.textContent = text; b.onclick = () => { try { fn(); } catch (e) { toast('Lỗi nút test: ' + e.message); console.error(e); } b.blur(); }; r.appendChild(b); return b; };
  const ready = () => { if (!S.need || ['title', 'pickEgg', 'pickPet', 'egg'].includes(S.mode)) { toast('Vào phòng nuôi trước đã (chơi mới hoặc tiếp tục)'); return false; } return true; };
  const home = () => { S.mode = 'room'; S.stats = null; S.popupGoal = 0; S.pickerGoal = 0; S.act = null; S.walk = null; S.px = 320; };
  const STAGE_NAME = { baby: 'Con', child: 'Nhi', teen: 'Thiếu niên', adult: 'Trưởng thành', legend: 'Huyền thoại',
                       adult4: 'Trưởng thành 4 chân', legend4: 'Huyền thoại 4 chân' };
  const setStage = st => {
    S.stage = st; S.xp = 0; S.askedKey = null;
    if (LV[st]) S.level = LV[st][0];
    S.pool = undefined;
    home();
    if (has('greet')) act('greet');
  };

  // growing up
  let r = row('Tiến hóa');
  btn(r, 'Tiến hóa ngay (xem cảnh)', () => {
    if (!ready()) return;
    const to = nextStage();
    if (!to) return toast('Đã là bậc cuối');
    S.evoFrom = S.stage; S.evoTo = to; S.night = S.nightGoal = 0; S.popupGoal = 0;
    fadeTo(() => { S.mode = 'evo'; S.t0 = performance.now(); S.waitA = false; });
  });
  btn(r, 'Lên cấp tối đa của bậc', () => {
    if (!ready() || !LV[S.stage]) return;
    S.level = LV[S.stage][1]; S.xp = STAGE_EXP[S.stage]; S.askedKey = null; home();
    toast(`Lv ${S.level}: bảng tiến hóa sẽ hiện`);
  });
  btn(r, 'Đủ điều kiện (Linh khí, tim)', () => {
    if (!ready()) return;
    S.lk[EL()] = 100; S.tim = 5; S.askedKey = null; toast('Linh khí 100, đủ 5 tim');
  });
  btn(r, '+1 cấp', () => { if (ready()) { S.pool = 1e9; gainExp(STAGE_EXP[S.stage] / Math.max(1, LV[S.stage][1] - LV[S.stage][0])); S.pool = undefined; } });

  // the pet's form, and which pet
  const rStage = row('Đổi dạng pet (bậc)');
  const rPet = row('Đổi pet');
  const sel = document.createElement('select');
  rPet.appendChild(sel);
  const fillStages = () => {
    rStage.querySelectorAll('button').forEach(b => b.remove());
    for (const st of DATA.order || Object.keys(DATA.stages)) btn(rStage, STAGE_NAME[st] || st, () => { if (ready()) setStage(st); });
  };
  btn(rPet, 'Đổi', () => {
    if (!ready()) return;
    const id = sel.value;
    toast('Đang tải pet…');
    loadCreature(id).then(() => {
      if (!DATA.stages[S.stage]) S.stage = 'baby';
      setStage(S.stage); fillStages(); toast(`Giờ là ${DATA.creature_name}`);
    });
  });

  // where it lives
  r = row('Đổi bối cảnh (nhà)');
  const houseSel = document.createElement('select');
  r.appendChild(houseSel);
  btn(r, 'Chuyển tới', () => {
    if (!ready()) return;
    const i = +houseSel.value;
    S.homes[i] = true; S.house = i; S.fresh = []; S.poops = []; S.mess = []; home();
    toast(`Chuyển tới ${houseSel.options[houseSel.selectedIndex].text}`);
  });
  btn(r, 'Mua hết đồ trang trí nhà này', () => {
    if (!ready()) return;
    const h = DATA.houses[S.house];
    for (const d of h.items || []) S.placed[h.key + ':' + d.id] = true;
    toast('Đã có hết đồ của nhà này');
  });
  btn(r, 'Ngày / đêm (ngủ)', () => { if (ready()) { home(); S.nightGoal = S.nightGoal ? 0 : 1; if (S.nightGoal) { S.sleepT = performance.now(); act('sleep', { hold: true }); } } });

  // screens
  r = row('Tới màn');
  const go = (name, fn) => btn(r, name, () => { if (ready()) { home(); fadeTo(fn); } });
  go('Phòng', () => {});
  go('Bản đồ', () => openMap());
  go('Chợ', () => { S.mode = 'shop'; S.tab = 0; S.item = 0; });
  go('Hoạt động', () => { S.mode = 'act'; S.actSel = 0; });
  go('Câu cá', () => { S.mode = 'fish'; S.fish = { st: 'ready', t: performance.now() }; });
  go('Nông trại', () => { S.mode = 'farm'; S.farmSel = Math.max(0, plotAt(4, 1)); S.seed = Math.max(0, SEEDS.findIndex(x => x.he === EL())); S.fx = null; });
  btn(r, 'Chỉ số', () => { if (ready()) { home(); S.stats = 0; } });
  btn(r, 'Màn tiêu đề', () => { fadeTo(() => { S.mode = 'title'; }); });

  // needs, money, time
  r = row('Chỉ số và tiền');
  const needs = v => { if (ready()) { Object.assign(S.need, v); toast('Đã đặt chỉ số'); } };
  btn(r, 'Đầy hết', () => { needs({ no: 100, vui: 100, sach: 100, nl: 100 }); S.sick = false; S.poops = []; S.mess = []; });
  btn(r, 'Đói', () => needs({ no: 10 }));
  btn(r, 'Buồn', () => needs({ vui: 10 }));
  btn(r, 'Bẩn', () => needs({ sach: 15 }));
  btn(r, 'Mệt', () => needs({ nl: 8 }));
  btn(r, 'Ốm', () => { if (ready()) { S.sick = true; emote('bc_choang'); } });
  btn(r, 'Hết ốm', () => { if (ready()) S.sick = false; });
  btn(r, '+5.000 vàng', () => { if (ready()) S.coins += 5000; });
  btn(r, '+1 Ngọc Hồn', () => { if (ready()) S.ngoc++; });
  r = row('Tua thời gian (như đi vắng)');
  for (const [t, h] of [['+1 giờ', 1], ['+8 giờ', 8], ['+1 ngày', 24]])
    btn(r, t, () => { if (ready() && __tuaGio(h * 3600e3)) toast(`Đã qua ${t.slice(1)}`); });

  // fill the lists once the game data is in, keep a line of state under the buttons
  let pet = '';
  setInterval(() => {
    if (!sel.options.length && DATA.creatures) for (const c of DATA.creatures) sel.add(new Option(`${c.name} (${c.element})`, c.id));
    if (!houseSel.options.length && DATA.houses) DATA.houses.forEach((h, i) => houseSel.add(new Option(`${h.name || h.key} · Lv${h.tier || '?'}`, i)));
    const key = DATA.pet && DATA.order ? DATA.pet.creature + DATA.order.join() : '';
    if (key && key !== pet) { pet = key; sel.value = DATA.pet.creature; fillStages(); }
    if (S.need) {
      const n = S.need, f = v => Math.round(v);
      state.textContent = `${DATA.creature_name || ''} · ${STAGE_NAME[S.stage] || S.stage} · Lv ${S.level} · EXP ${f(S.xp)}/${STAGE_EXP[S.stage] || '-'}` +
        ` · kho EXP ${S.pool === undefined ? '-' : f(S.pool)}\nNo ${f(n.no)} · Vui ${f(n.vui)} · Sạch ${f(n.sach)} · Năng lượng ${f(n.nl)}` +
        `${S.sick ? ' · ỐM' : ''} · ${S.coins} vàng · màn ${S.mode}`;
    }
  }, 500);
})();
