// Elemon: the pet talks. A speech bubble over its head in the room when it is fed, petted, played with, put to bed,
// woken, trained, comes home; now and then on its own, about how it feels (hungry, sleepy, dirty, sick, bored, fine).
// How it talks grows with it (the user, 31/10/2026: sweet at first, a bit more with each stage, the Huyền thoại the
// rudest of all):
//   baby   babbles, calls itself by name, "chủ ơi"
//   child  sweet, "em" and "chủ"
//   teen   cheeky, "tui"
//   adult  cool and dry, "tôi" and "cậu"
//   legend rude and full of itself, "tao"/"bổn tọa" and "mày"/"con sen"
// {ten} is the pet's name. The lines change here only; the demo's own thought bubbles (S.bubble) stay as they are.
(() => {
  if (typeof press !== 'function' || typeof frame !== 'function' || typeof act !== 'function' || typeof drawPet !== 'function') return;
  const LOI = {
    baby: {
      chao: ['Chủ ơi! {ten} nhớ chủ!', 'A, chủ về rồi!', 'Ôm {ten} đi chủ!'],
      an: ['Măm măm… ngon quá!', 'Nữa, nữa đi chủ!', '{ten} no căng bụng rồi nè'],
      an_thich: ['Món {ten} thích nhất nè!', 'Ngon ngon ngon!!'],
      tu_choi: ['Ứ ừ… {ten} hông ăn đâu', 'Dở lắm, hông chịu!'],
      vuot: ['Hi hi, nhột quá!', 'Thích ghê á!', 'Chủ thương {ten} hông?'],
      bat_mat: ['Huhu… đủ rồi mà…', '{ten} giận rồi đó!'],
      choi: ['Chơi nữa đi chủ!', 'Hí hí, vui quá!', 'Thương chủ nhất!'],
      ngu: ['Chủ ngủ ngon nha…', '{ten} buồn ngủ… oáp'],
      day: ['Oáp… sáng rồi hả chủ?', '{ten} dậy rồi nè!'],
      tap: ['{ten} mạnh lên chưa chủ?', 'Mệt mà vui!'],
      doi: ['Bụng {ten} kêu ọt ọt…', 'Chủ ơi, {ten} đói…'],
      buon_ngu: ['Mắt {ten} díp lại rồi…', 'Cho {ten} đi ngủ nha'],
      ban: ['{ten} hôi hôi rồi…', 'Tắm cho {ten} đi chủ'],
      om: ['{ten} mệt quá… chủ ơi…', 'Đau đau…'],
      buon: ['Chủ chơi với {ten} đi…', '{ten} buồn xo…'],
      // hints (the user, 02/11/2026: complaints that tell you what to do): {mon} a dish of its element sold at Chợ,
      // {do} the next thing the room lacks, {nha} the home to move to next, {viec} somewhere to go
      them: ['{ten} thèm {mon} quá à…', 'Chủ ơi, mua {mon} cho {ten} nha?', 'Ọt ọt… {ten} muốn ăn {mon}!'],
      thieu_do: ['Nhà mình thiếu {do} nè chủ', '{ten} muốn có {do}!'],
      nha_moi: ['Chủ ơi, mình dọn qua {nha} đi!', '{ten} muốn ở {nha} cơ!'],
      muon_di: ['Chủ ơi, đi {viec} hông?', '{ten} muốn đi {viec}!'],
      het_do_choi: ['Bóng hỏng rồi… chủ mua bóng mới cho {ten} nha', '{ten} hông có gì chơi hết…'],
      vui: ['La la la~', '{ten} thương chủ!', 'Hôm nay vui ghê!', 'Chủ thấy {ten} lớn chưa?'],
    },
    child: {
      chao: ['Chủ về rồi! Em chờ mãi!', 'Hôm nay chủ đi đâu vậy?'],
      an: ['Ngon quá, cảm ơn chủ!', 'Em ăn sạch luôn!'],
      an_thich: ['Đúng món em thích! Chủ hiểu em ghê', 'Món ruột của em nè!'],
      tu_choi: ['Em không ăn món này đâu…', 'Món này em ghét lắm…'],
      vuot: ['Hi hi, chỗ đó đó!', 'Em thích được vuốt lắm!'],
      bat_mat: ['Thôi mà, xù lông hết rồi!', 'Đủ rồi chủ ơi!'],
      choi: ['Ném nữa đi, em bắt được hết!', 'Vui quá trời!'],
      ngu: ['Ngủ ngon nha chủ', 'Mai mình chơi tiếp nhé'],
      day: ['Sáng rồi! Đi chơi thôi!', 'Em ngủ ngon lắm'],
      tap: ['Hôm nay em mạnh hơn hôm qua!', 'Em sẽ thành tinh linh mạnh nhất!'],
      doi: ['Chủ ơi, em đói rồi', 'Có gì ăn không chủ?'],
      buon_ngu: ['Em buồn ngủ quá…', 'Cho em ngủ chút nha'],
      ban: ['Người em bẩn rồi, tắm đi chủ', 'Em ngứa quá à'],
      om: ['Em không khỏe… cho em uống thuốc nha', 'Em mệt lắm chủ ơi'],
      buon: ['Chủ quên em rồi hả…', 'Chơi với em một xíu đi'],
      them: ['Em thèm {mon} quá chủ ơi', 'Hôm nay ăn {mon} được không chủ?', 'Ra Chợ mua {mon} cho em nha!'],
      thieu_do: ['Phòng mình còn thiếu {do} đó chủ', 'Có {do} thì nhà đẹp hơn nhiều!'],
      nha_moi: ['Nhà này chật quá, mình chuyển qua {nha} đi chủ', 'Em mơ được ở {nha} lắm!'],
      muon_di: ['Mình đi {viec} đi chủ!', 'Ở nhà hoài chán, đi {viec} nha?'],
      het_do_choi: ['Hết bóng rồi chủ ơi, ra Chợ mua quả mới nha', 'Em muốn chơi mà không có bóng…'],
      vui: ['Chủ là nhất!', 'Em lớn rồi đó nha!', 'Hôm nay trời đẹp ghê', 'Em muốn ra ngoài chơi!'],
    },
    teen: {
      chao: ['Ờ, về rồi đó hả.', 'Đi lâu thế, tui chán muốn xỉu.'],
      an: ['Tạm được.', 'Ăn thì ăn, mà lần sau đổi món nha.'],
      an_thich: ['Ồ, biết điều đấy!', 'Cái này mới gọi là đồ ăn.'],
      tu_choi: ['Ai thèm ăn cái đó.', 'Cất đi, nhìn đã ngán.'],
      vuot: ['Thôi được, cho vuốt chút.', 'Đừng kể ai là tui thích nha.'],
      bat_mat: ['Bộ rảnh lắm hả?', 'Đủ rồi, phiền ghê!'],
      choi: ['Trò con nít… mà thôi, chơi tiếp!', 'Ném xa hơn coi!'],
      ngu: ['Tắt đèn đi, chói mắt.', 'Đừng có gọi tui dậy sớm.'],
      day: ['Gọi gì sớm vậy trời…', 'Năm phút nữa thôi…'],
      tap: ['Dễ ợt.', 'Thấy tui mạnh lên chưa?'],
      doi: ['Đói rồi, có định cho ăn không đây?', 'Bụng kêu nãy giờ đó.'],
      buon_ngu: ['Buồn ngủ, đừng làm phiền.', 'Tui đi ngủ đây.'],
      ban: ['Ghê quá, tắm cho tui đi.', 'Dơ thế này sao ra đường.'],
      om: ['Tui… hơi mệt. Không phải than đâu nha.', 'Thuốc đâu… nhanh lên.'],
      buon: ['Chán. Chán thật sự.', 'Không ai chơi với tui hết.'],
      them: ['Thèm {mon} muốn xỉu.', 'Mua {mon} đi, đừng có keo.', 'Ăn hoài đồ cũ, tui muốn {mon}.'],
      thieu_do: ['Nhà gì thiếu cả {do}.', 'Kiếm cái {do} về coi, trống trơn à.'],
      nha_moi: ['Ở đây hoài quê lắm. Lên {nha} đi.', 'Bạn tui ở {nha} hết rồi đó.'],
      muon_di: ['Đi {viec} đi, ngồi nhà mốc meo rồi.', 'Bao giờ mới đi {viec} vậy?'],
      het_do_choi: ['Bóng đâu? Hết rồi thì ra Chợ mua đi chứ.', 'Không có đồ chơi thì chơi cái gì?'],
      vui: ['Tui ngầu nhất cái nhà này.', 'Tâm trạng đang tốt, đừng phá.', 'Bao giờ mới được ra ngoài đánh nhau?'],
    },
    adult: {
      chao: ['Cậu về rồi. Tốt.', 'Tôi giữ nhà giúp cậu đấy.'],
      an: ['Đủ năng lượng rồi.', 'Không tệ.'],
      an_thich: ['Món này mới xứng với tôi.', 'Cậu chọn khéo đấy.'],
      tu_choi: ['Không. Tôi có nguyên tắc.', 'Đem đi đi.'],
      vuot: ['…Được rồi, chút thôi.', 'Cậu cũng có lúc dễ thương.'],
      bat_mat: ['Tôi không phải thú bông.', 'Dừng lại. Ngay.'],
      choi: ['Hừ, chỉ vì cậu thôi đấy.', 'Lâu rồi mới vui thế này.'],
      ngu: ['Ngủ đi. Mai còn việc.', 'Canh nhà giùm tôi.'],
      day: ['Tôi dậy rồi. Đi đâu?', 'Một ngày mới. Chiến thôi.'],
      tap: ['Chưa đủ. Thêm nữa.', 'Khói Hư đang chờ.'],
      doi: ['Tôi cần ăn. Bây giờ.', 'Bụng đói thì đánh sao nổi.'],
      buon_ngu: ['Tôi cần nghỉ.', 'Mắt nặng quá rồi.'],
      ban: ['Bộ dạng này không hợp với tôi.', 'Tôi cần tắm.'],
      om: ['Bệnh vặt thôi… không sao… khụ.', 'Lấy thuốc giúp tôi.'],
      buon: ['Cậu bận quá nhỉ.', 'Nhà vắng thật.'],
      them: ['Tôi cần {mon}. Ở Chợ có bán.', 'Hôm nay tôi muốn {mon}.'],
      thieu_do: ['Căn phòng thiếu {do}.', 'Thêm {do} thì tôi ở yên hơn.'],
      nha_moi: ['Đến lúc chuyển lên {nha} rồi.', 'Nơi này không còn hợp với tôi. {nha} thì được.'],
      muon_di: ['Đi {viec}. Tôi cần vận động.', 'Ngồi yên lâu quá. {viec} chứ?'],
      het_do_choi: ['Hết bóng. Chợ có bán.', 'Không có đồ chơi thì tôi tập một mình vậy.'],
      vui: ['Khói Hư không làm gì được tôi.', 'Tôi mạnh hơn nhiều rồi.', 'Cậu nuôi tôi khéo đấy.'],
    },
    legend: {
      chao: ['Ồ, con sen về rồi đấy à.', 'Đi đâu giờ mới về? Bổn tọa đói rã họng.', 'Lại cái mặt này.'],
      an: ['Ăn tạm cho mày vui.', 'Lần sau mua đồ xịn hơn, đồ keo kiệt.', 'Nhai mỏi cả mồm.'],
      an_thich: ['Hừ, cuối cùng cũng biết điều.', 'Được. Hôm nay tha cho mày.'],
      tu_choi: ['Cái thứ này mà cũng dám dâng lên?', 'Vứt. Ngay. Đi.', 'Mày đùa với Huyền thoại à?'],
      vuot: ['Rửa tay chưa mà sờ?', 'Ai cho mày chạm vào bổn tọa?', 'Gãi bên trái. Trái của TAO.'],
      bat_mat: ['Sờ nữa là tao đốt nhà đấy.', 'Muốn ăn đòn không?', 'Cút ra!'],
      choi: ['Trò con nít. Ném lại coi.', 'Tao chơi vì thương hại mày thôi.', 'Ném dở thế, tập thêm đi.'],
      ngu: ['Tắt đèn. Cấm ngáy.', 'Đứa nào đánh thức tao là xong đời.'],
      day: ['Ai cho gọi bổn tọa dậy?!', 'Thấy mặt mày từ sáng là biết hôm nay xui.'],
      tap: ['Cọc gì mà yếu xìu, đổi đồ khác đi.', 'Tao đánh một phát là sập võ đường.'],
      doi: ['Con sen đâu?! Tao đói!', 'Định bỏ đói Huyền thoại à? Gan nhỉ.'],
      buon_ngu: ['Biến ra cho tao ngủ.', 'Im lặng. Bổn tọa nghỉ.'],
      ban: ['Nhà gì như cái chuồng. Dọn đi!', 'Tắm cho tao. Nước ấm. Nhanh.'],
      om: ['Khụ… nhìn gì… lấy thuốc mau lên…', 'Tao mà chết là tại mày đấy…'],
      buon: ['Chán mày quá.', 'Bỏ bê tao đấy à? Được lắm.'],
      them: ['Con sen, ra Chợ mua {mon} cho tao. Ngay.', 'Bổn tọa thèm {mon}. Còn đứng đó à?', 'Không có {mon} thì đừng về.'],
      thieu_do: ['Nhà không có nổi cái {do}. Nhục.', 'Mua {do} về, đừng để tao nhắc lần hai.'],
      nha_moi: ['Huyền thoại mà ở cái ổ này à? Lên {nha} mau.', 'Tao chỉ ở {nha}. Lo mà kiếm tiền.'],
      muon_di: ['Dẫn tao đi {viec}. Ngồi đây mục xương rồi.', '{viec}. Đi. Bây giờ.'],
      het_do_choi: ['Mày bắt tao chơi với không khí à? Mua bóng!', 'Bóng hỏng rồi. Chợ. Ngay.'],
      vui: ['Thiên hạ này là của tao.', 'Ngũ Hành á? Tao một mình cũng đủ.', 'Được nuôi tao là phúc ba đời nhà mày.', 'Quỳ xuống mà chiêm ngưỡng.'],
    },
  };
  // what the pet does -> what it says (eating its favourite: the demo has just set its heart bubble)
  const ON_ACT = { greet: 'chao', wave: 'chao', eat: () => S.bubble === 'bong_tim' ? 'an_thich' : 'an', refuse: 'tu_choi',
                   petted: 'vuot', angry: 'bat_mat', happy: x => x && x.toy !== undefined ? 'choi' : null,
                   sleep: 'ngu', wake: 'day', train: 'tap' };
  const ALWAYS = new Set(['chao', 'ngu', 'day', 'bat_mat', 'tu_choi', 'het_do_choi']);    // said even right after another line
  const SAY_MS = 2600, PER_CHAR_MS = 45;                 // how long a line stays: a base and a bit a letter
  const ALONE_MS = [22e3, 40e3];                         // on its own: once in this long, while nothing happens
  const PET_EVERY = 6000;                                // petting: one line in this long at most
  const W_MAX = 230, FONT = 'bold 14px Tahoma, sans-serif', LH = 18, PAD = 9;

  const stageOf = () => ({ adult4: 'adult', legend4: 'legend' })[S.stage] || S.stage;
  let last = {}, said = null, nextAlone = 0, petT = -1e9, box = null;
  function say(kind, now = performance.now(), vars = null) {
    const set = (LOI[stageOf()] || {})[kind];
    if (!set || !set.length || (globalThis.CAI_DAT && CAI_DAT.noi === false)) return;   // Cài đặt: Pet nói chuyện (man-chao.js)
    if (!ALWAYS.has(kind) && said && now - said.t < said.ms * 0.6) return;
    let i = Math.floor(Math.random() * set.length);
    if (set.length > 1 && i === last[kind]) i = (i + 1) % set.length;
    last[kind] = i;
    const s = set[i].replace(/\{ten\}/g, DATA.pet.name).replace(/\{(mon|do|nha|viec)\}/g, (m, k) => (vars && vars[k]) || m);
    said = { s, t: now, ms: SAY_MS + s.length * PER_CHAR_MS, legend: stageOf() === 'legend' };
    nextAlone = now + ALONE_MS[0] + Math.random() * (ALONE_MS[1] - ALONE_MS[0]);
  }
  globalThis.__noi = say;                                 // for the test harness
  globalThis.__noiGoiY = () => ({ them: craving(), nha: house(), di: outing() });
  globalThis.__noiDa = () => said && said.s;

  const act0 = act;
  globalThis.act = function (anim, extra) {
    const r = act0.apply(this, arguments);
    if (S.mode !== 'room') return r;
    let k = ON_ACT[anim];
    if (typeof k === 'function') k = k(extra);
    if (k === 'vuot') { const now = performance.now(); if (now - petT < PET_EVERY) return r; petT = now; }
    if (k) say(k);
    return r;
  };
  // X at a stage drawn without a petting move: the demo only says so, the pet still answers
  const press0 = press;
  globalThis.press = function (btn) {
    const room = S.mode === 'room' && S.stats === null && S.fade === 0 && S.popupGoal === 0 && S.pickerGoal === 0 &&
      !(S.truyen && S.truyen.dang);
    const r = press0.apply(this, arguments);
    if (room && btn === 'X' && !has('petted') && !(S.act && S.act.anim === 'angry')) {
      const now = performance.now();
      if (/chưa có động tác vuốt ve/.test(S.toast || '')) S.toast = null;    // its answer says enough
      if (now - petT >= PET_EVERY) { petT = now; say('vuot', now); }
    }
    return r;
  };
  // where the pet is: the box the room's drawPet returns
  const pet0 = drawPet;
  globalThis.drawPet = function () {
    const b = pet0.apply(this, arguments);
    if (S.mode === 'room' && S.stats === null && b) box = b;
    return b;
  };

  const calm = () => S.mode === 'room' && S.stats === null && S.fade === 0 && S.popup < 0.05 && S.picker < 0.05 &&
    !(S.truyen && S.truyen.dang);
  // ---------- the hints: what the pet asks for (each null when there is nothing to ask) ----------
  const HE = { hoa: 'Hỏa', kim: 'Kim', moc: 'Mộc', thuy: 'Thủy', tho: 'Thổ' };
  const pick = a => a.length ? a[Math.floor(Math.random() * a.length)] : null;
  const low = w => w.charAt(0).toLowerCase() + w.slice(1);           // a dish or a thing, said mid-line (homes keep their names)
  // a dish of its own element (its favourite kind: the demo's heart bubble) from Chợ's food tab
  function craving() {
    const he = HE[DATA.pet.element], rows = DATA.shop && DATA.shop.rows ? DATA.shop.rows.flat() : [];
    const r = pick(rows.filter(r => r && r.he === he && r.name && r.file && /^[A-Z][a-z]+_\d/.test(r.file)));
    return r ? { mon: low(r.name) } : null;
  }
  // the home: a thing its room still lacks, else the next home up (its own element's first) once it may be had
  function house() {
    if (typeof HOME !== 'function' || typeof isPlaced !== 'function' || !S.homes) return null;
    const h = HOME();
    if (!h) return null;
    const lack = h.items.filter(d => !isPlaced(h, d.id));
    if (lack.length) return { kind: 'thieu_do', do: low(pick(lack).name) };
    const next = DATA.houses.map((n, i) => [n, i]).filter(([n, i]) => n.tier === h.tier + 1 && !S.homes[i] &&
      (typeof houseNeed !== 'function' || !houseNeed(i)));
    if (!next.length) return null;
    const own = next.filter(([n]) => n.he === HE[DATA.pet.element]);
    return { kind: 'nha_moi', nha: (own.length ? own : next)[0][0].name };
  }
  // somewhere to go (a Con stays in the village: Vùng đất is for the bigger ones)
  function outing() {
    const go = ['câu cá', 'trồng rau', 'học ở trường', 'Võ đường tập'];
    if (S.stage !== 'baby') go.push('Vùng đất', 'Võ đường đấu Solo');
    return { viec: pick(go) };
  }
  function alone(now) {                                   // a line of its own, from how it feels
    if (!nextAlone) { nextAlone = now + 8000; return; }
    if (now < nextAlone || S.act || S.walk || S.night > 0.05) return;
    const n = S.need;
    if (S.sick) return say('om', now);
    if (n.no < 30) { const c = craving(); return c && Math.random() < 0.5 ? say('them', now, c) : say('doi', now); }
    if (n.nl < 20) return say('buon_ngu', now);
    if (n.sach < 30) return say('ban', now);
    if (n.vui < 30) {                                   // bored: no toy left is the first thing to say (song-that.js)
      if (S.items && !(S.bongLuot > 0) && !S.items.some((it, i) => it.use === 'ball' && S.bag[i] > 0) && Math.random() < 0.6) return say('het_do_choi', now);
      return Math.random() < 0.5 ? say('muon_di', now, outing()) : say('buon', now);
    }
    // nothing wrong: now and then a wish (a dish, the home, an outing), else it is just happy
    const r = Math.random(), h = r < 0.3 && house(), c = r >= 0.3 && r < 0.5 && n.no < 80 && craving();
    if (h) return say(h.kind, now, h);
    if (c) return say('them', now, c);
    if (r >= 0.5 && r < 0.65) return say('muon_di', now, outing());
    say('vui', now);
  }
  function lines(s) {                                     // the line broken to fit W_MAX
    ctx.font = FONT;
    const out = [];
    let cur = '';
    for (const w of s.split(' ')) {
      const t = cur ? cur + ' ' + w : w;
      if (cur && ctx.measureText(t).width > W_MAX) { out.push(cur); cur = w; } else cur = t;
    }
    if (cur) out.push(cur);
    return out;
  }
  function bubble(now) {
    const age = now - said.t, b = box;
    if (age > said.ms || !b) return;
    const ls = lines(said.s);
    ctx.font = FONT;
    const w = Math.ceil(Math.max(...ls.map(l => ctx.measureText(l).width))) + 2 * PAD, h = ls.length * LH + 2 * PAD - 4;
    const hx = b.x + b.w / 2, top = Math.max(44, b.y - 18 - h);
    // left of the head (the demo's thought bubble sits to its right), the tail down to the head
    const x = Math.round(Math.max(8, Math.min(632 - w, hx - w + 34))), y = Math.round(top);
    const pop = Math.min(1, age / 120), fade = Math.min(1, (said.ms - age) / 300);
    ctx.save();
    ctx.globalAlpha = fade;
    const tx = Math.max(x + 14, Math.min(x + w - 14, hx - 6)), ty = y + h;
    const fill = said.legend ? '#fff0e6' : '#fffaf0', edge = said.legend ? '#7a1c10' : '#1a0c06';
    ctx.fillStyle = edge;
    ctx.fillRect(x - 2, y - 2 + (1 - pop) * 6, w + 4, h + 4);
    ctx.beginPath(); ctx.moveTo(tx - 9, ty); ctx.lineTo(tx + 9, ty); ctx.lineTo(tx + 2, ty + 14); ctx.closePath(); ctx.fill();
    ctx.fillStyle = fill;
    ctx.fillRect(x, y + (1 - pop) * 6, w, h);
    ctx.beginPath(); ctx.moveTo(tx - 6, ty - 1); ctx.lineTo(tx + 6, ty - 1); ctx.lineTo(tx + 2, ty + 10); ctx.closePath(); ctx.fill();
    ls.forEach((l, i) => text(l, x + PAD, y + PAD + 6 + i * LH + (1 - pop) * 6, 14, said.legend ? '#8a1e0e' : '#3a2412', 'left', true, 0));
    ctx.restore();
  }

  const frame0 = frame;
  globalThis.frame = function (now) {
    box = null;
    const r = frame0.apply(this, arguments);
    if (calm()) { alone(now); if (said) bubble(now); }
    return r;
  };
})();
