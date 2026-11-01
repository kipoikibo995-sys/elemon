// Elemon: lời thoại cốt truyện (bản "Elemon — Cốt truyện và 5 vùng đất", 26/10/2026). Chỉ có chữ: sửa lời ở đây,
// không phải đụng code. Hộp thoại đọc file này là game/src/hoi-thoai.js.
//
// NPC: tên hiện trên bảng tên, màu bảng tên, và ảnh chân dung theo biểu cảm (đường dẫn trong img/, không có .png).
//   Biểu cảm chưa có ảnh thì hộp thoại không vẽ chân dung, chữ chiếm cả hộp.
// CANH: các cảnh, mỗi cảnh chỉ chạy một lần (đã xem thì lưu trong S.truyen.da).
//   khi:  màn hình mở cảnh: 'egg' (ấp trứng), 'room' (trong nhà), 'map' (bản đồ), 'school' (Trường học),
//         'seedShop' (quầy Bác Sóc), 'voduong' (Võ đường), 'vungdat' (cổng vùng đất cùng hệ với pet),
//         'phim' (cảnh có thoai trong PHIM gọi tới)
//   cap:  chỉ chạy khi pet đang ở các cấp này (bỏ trống: cấp nào cũng được)
//   lv:   level tối thiểu (bỏ trống: 0)
//   cau:  các câu [ai, biểu cảm, lời]. ai = null: lời dẫn truyện (chữ nghiêng, không bảng tên).
//         Pet không nói, chỉ được tả qua lời dẫn truyện.
// Chữ thay tự động: {pet} tên pet, {he} hệ của pet (Hỏa...), {vung} vùng đất của hệ đó (Núi lửa...).
// Giọng đọc (scripts/make_giong.py, giọng tiếng Việt của Microsoft qua edge-tts): giong = [giọng, tốc độ, độ cao,
//   xử lý thêm nếu có: 'noi-luc' = trầm thêm, dày và vang; 'gia' = giọng ông lão, hơi rung; 'vo-su' = chắc, dứt khoát; cách đọc nếu có: 'ke-chuyen' = đọc từng cụm,
//   ngắt hơi theo dấu câu, đầu câu cao hơn, cuối câu thấp và chậm lại]
//   Già Quy: giọng ElevenLabs tự thiết kế (tên 'Già Quy (Elemon)' trong tài khoản cũ, đã mất); câu mới từ 30/10/2026
//   (Hồi 3 trở đi, Sức khỏe, Đài Ngũ Hành) thu bằng giọng cộng đồng 'Bob - Deep & Calm Northern Vietnamese'; Sư phụ: giọng cộng đồng
//   'Tuan Anh - Deep, Powerful, Professional'; Cô Rắn: 'Giang - Northern female Narrator'; Bác Sóc: 'Tram - Friendly
//   Southern Vietnamese' (giọng cộng đồng của ElevenLabs); lời dẫn: 'Bà lão kể chuyện (Elemon)' tự thiết kế. Cả năm tạo tay trên elevenlabs.io;
//   sửa lời của ông thì chạy script, nó liệt kê câu cần tạo lại, rồi nhập bằng --nhap (xem đầu scripts/make_giong.py).
//   giọng: 'vi-VN-HoaiMyNeural' (nữ) hoặc 'vi-VN-NamMinhNeural' (nam); tốc độ '-10%'...; độ cao '-6Hz'...
//   Giọng đọc bỏ phần trong ngoặc (R2), (X) và đọc {pet} là "bé". Sửa lời xong chạy lại script là có giọng mới.
// Mỗi câu nên dưới ~130 chữ cái (3 dòng); dài hơn thì hộp tự chia trang, bấm A để sang trang.
globalThis.TRUYEN = {
  // giọng lời dẫn truyện (câu ai = null và chữ chạy trong phim)
  // bà lão kể chuyện, mấy trăm tuổi: giọng ElevenLabs tự thiết kế 'Bà lão kể chuyện (Elemon)'; lời đưa vào ElevenLabs có
  // thẻ cảm xúc ([sighs], [coughs], [whispers]...), xem assets/am-thanh/dan-elevenlabs_loi-the.txt
  // (bản cũ: ['vi-VN-NamMinhNeural', '-16%', '-14Hz', 'noi-luc', 'ke-chuyen'])
  DAN: { giong: ['elevenlabs', 'Bà lão kể chuyện (Elemon)'] },
  NPC: {
    'gia-quy': { ten: 'Già Quy', mau: '#5f8f4e', giong: ['elevenlabs', 'Già Quy (Elemon)'],
      // sheet gốc assets/source/npc/NPC_gia-quy.png, game/build_game.py cắt ra (NPC_FACES, đúng thứ tự này)
      anh: { cuoi: 'npc/gia-quy_1-cuoi', 'ke-chuyen': 'npc/gia-quy_2-ke-chuyen', 'gio-gay': 'npc/gia-quy_3-gio-gay',
             'ngac-nhien': 'npc/gia-quy_4-ngac-nhien', 'lo-lang': 'npc/gia-quy_5-lo-lang', 'chi-xa': 'npc/gia-quy_6-chi-xa',
             'gat-dau': 'npc/gia-quy_7-gat-dau', buon: 'npc/gia-quy_8-buon' } },
    'co-ran': { ten: 'Cô Rắn', mau: '#4f9a5a', giong: ['elevenlabs', 'Giang - Northern female Narrator'],
      anh: { cuoi: 'th_co_1-cuoi', 'chop-mat': 'th_co_2-chop-mat', giang: 'th_co_3-giang', khen: 'th_co_4-khen',
             'suy-nghi': 'th_co_5-suy-nghi', 'ngac-nhien': 'th_co_6-ngac-nhien', sai: 'th_co_7-sai' } },
    'bac-soc': { ten: 'Bác Sóc', mau: '#b0703a', giong: ['elevenlabs', 'Tram - Friendly Southern Vietnamese'],
      anh: { cuoi: 'sn_chu_1-cuoi', chao: 'sn_chu_3-chao', 'cuoi-lon': 'sn_chu_4-cuoi-lon', 'suy-nghi': 'sn_chu_5-suy-nghi',
             'dua-hat': 'sn_chu_6-dua-hat', 'cam-on': 'sn_chu_8-cam-on' } },
    'su-phu': { ten: 'Sư phụ', mau: '#a8483a', giong: ['elevenlabs', 'Tuan Anh - Deep, Powerful, Professional'],
      anh: { cuoi: 'vd/ne/su-phu_cuoi', dung: 'vd/ne/su-phu_dung', 'lay-da': 'vd/ne/su-phu_lay-da',
             'ngac-nhien': 'vd/ne/su-phu_ngac-nhien', 'that-vong': 'vd/ne/su-phu_that-vong' } },
  },

  // Phim (game/src/phim.js), hai cuộn: 'mo-dau' khi bấm Chơi mới (rồi tới màn chọn trứng), 'dem-ay' khi đã chọn
  // xong trứng (rồi tới màn ấp trứng). START bỏ qua cả cuộn, A sang cảnh sau.
  //   nen:   ảnh nền: 'map' (bản đồ thế giới) hoặc tên ảnh phim (assets/source/phim/<tên>.png, 16:9)
  //   cam:   [zoom, x, y] lúc đầu và lúc cuối cảnh; x, y là điểm giữa khung hình trên ảnh coi như rộng 640
  //          (bản đồ 640x480, ảnh phim 640x360); bỏ trống: đứng yên, thấy cả ảnh
  //   chop:  một chớp sáng trắng ở khoảng 3/4 cảnh
  //   ms:    thời gian tối thiểu của cảnh; chu: lời dẫn chạy ở dải đen phía dưới
  //   thoai: id một cảnh hội thoại ở CANH (khi: 'phim'): ảnh đứng yên cho tới khi nói xong
  PHIM: {
    'mo-dau': { sau: 'pickEgg', canh: [
      { nen: 'map', cam: [[1, 320, 240], [1.15, 320, 230]], ms: 6000,
        chu: 'Quần đảo Elemon. Nơi tinh linh năm hệ sống cùng con người, và Linh khí chảy trong từng ngọn núi, dòng sông.' },
      { nen: 'PHIM_1_hu-anh', cam: [[1.2, 320, 150], [1, 320, 180]], ms: 7000,
        chu: 'Ngàn năm trước, từ một khe nứt của đất trời, Hư Ảnh tràn ra: một bóng khói không thuộc hệ nào, nuốt sạch Linh khí của muôn loài.' },
      { nen: 'PHIM_2_than-thu', cam: [[1.25, 200, 200], [1.25, 440, 200]], ms: 7000,
        chu: 'Năm Thần thú hộ vùng đứng lên chống lại nó: Thủy Long, Kim Ưng, Thụ Nhân, Viêm Long và Thổ Long.' },
      { nen: 'PHIM_3_phong-an', cam: [[1, 320, 180], [1.3, 320, 175]], chop: true, ms: 7000,
        chu: 'Họ hợp sức phong ấn Hư Ảnh dưới Đài Ngũ Hành, rồi trở về canh giữ năm vùng đất.' },
      { nen: 'PHIM_4_dai-ngu-hanh', cam: [[1.25, 340, 200], [1, 320, 180]], ms: 7000,
        chu: 'Quanh Đài, Làng Ngũ Sắc mọc lên. Ngàn năm trôi qua, chuyện ấy chỉ còn là truyền thuyết… và phong ấn yếu dần.' },
      { nen: 'PHIM_4_dai-ngu-hanh', thoai: 'phim-gia-quy' },
    ] },
    'dem-ay': { sau: 'egg', canh: [
      { nen: 'PHIM_4_dai-ngu-hanh', thoai: 'trao-trung' },
      { nen: 'PHIM_5_phong-an-nut', cam: [[1, 320, 180], [1.3, 320, 160]], ms: 7000,
        chu: 'Đêm ấy, khi cả làng đã ngủ, Đài Ngũ Hành bỗng rung lên. Một vệt khói tím vọt lên, tách làm năm rồi bay về năm phía của quần đảo.' },
      { nen: 'PHIM_5_phong-an-nut', cam: [[1.3, 320, 160], [1.3, 320, 160]], thoai: 'dem-ay' },
    ] },
    // Đài Ngũ Hành (game/src/vung-dat.js plays them): 'dai-mo' the first time the pet goes up to the Đài (then the
    // fight with Hư Ảnh), 'dai-ket' after the first win (then the map). {pet} in a caption: the pet's name ("bé" read)
    'dai-mo': { sau: 'vg-hu', canh: [
      { nen: 'PHIM_4_dai-ngu-hanh', cam: [[1.25, 340, 200], [1.25, 340, 200]], thoai: 'dai-truoc' },
      { nen: 'PHIM_6_dat-ngoc', cam: [[1.2, 330, 200], [1, 320, 180]], ms: 7000,
        chu: 'Năm Ngọc Hồn trở về Đài Ngũ Hành. Viên cuối cùng vừa đặt lên trụ đá, năm luồng sáng nối lại thành ngôi sao năm cánh.' },
      { nen: 'PHIM_7_hu-anh-thuc', cam: [[1, 320, 200], [1.3, 320, 110]], chop: true, ms: 7000,
        chu: 'Phong ấn ngàn năm vỡ tung. Năm mảnh khói tím tụ lại làm một, và Hư Ảnh hiện nguyên hình trên Đài.' },
      { nen: 'PHIM_7_hu-anh-thuc_duoi', cam: [[1.25, 320, 240], [1, 320, 180]], ms: 6500,
        chu: '{pet} không lùi bước. Năm Thần thú đã được giải thoát, giờ chỉ còn lại chính Hư Ảnh.' },
    ] },
    'dai-ket': { sau: 'map', canh: [
      { nen: 'PHIM_8_ket', cam: [[1.25, 320, 110], [1, 320, 180]], ms: 8000,
        chu: 'Bình minh trở lại quần đảo Elemon. Khói tím tan hết, năm vùng đất xanh tươi như ngàn năm trước.' },
      { nen: 'PHIM_8_ket', cam: [[1, 320, 180], [1.35, 320, 220]], ms: 7500,
        chu: 'Năm Thần thú cúi đầu trước {pet}. Hư Ảnh đã bị phong ấn lại, lần này bằng sức của cả năm hệ.' },
      { nen: 'PHIM_8_ket', cam: [[1.35, 320, 220], [1.35, 320, 220]], thoai: 'dai-sau' },
    ] },
  },

  CANH: [
    // ---------- Phim 'mo-dau': Già Quy đón người mới ----------
    { id: 'phim-gia-quy', khi: 'phim', cau: [
      ['gia-quy', 'ngac-nhien', 'Một người lạ… Đã lâu lắm rồi mới có người tìm đến Làng Ngũ Sắc.'],
      ['gia-quy', 'cuoi', 'Ta là Già Quy, trưởng làng, cũng là người giữ Đài Ngũ Hành.'],
      ['gia-quy', 'ke-chuyen', 'Ở đây, ai cũng có một tinh linh đồng hành. Làng còn giữ những quả trứng của đủ năm hệ.'],
      ['gia-quy', 'chi-xa', 'Hãy chọn lấy một quả. Nó sẽ theo cháu suốt chặng đường phía trước.'],
    ] },
    // ---------- Phim 'dem-ay': trao trứng, rồi đêm phong ấn nứt ----------
    { id: 'trao-trung', khi: 'phim', cau: [
      ['gia-quy', 'gat-dau', 'Trứng hệ {he}… Lựa chọn tốt. Ủ nó cho ấm và trò chuyện với nó mỗi ngày.'],
      ['gia-quy', 'ke-chuyen', 'Trứng tinh linh nghe được tiếng người. Nó sẽ nở khi nó tin cháu.'],
    ] },
    { id: 'dem-ay', khi: 'phim', cau: [
      ['gia-quy', 'lo-lang', 'Phong ấn… nứt rồi sao?'],
      ['gia-quy', 'buon', 'Năm luồng… bay về năm vùng đất. Ngàn năm rồi, cuối cùng nó cũng tới.'],
    ] },

    // ---------- Mở đầu: Quả trứng ----------
    { id: 'mo-dau', khi: 'egg', cau: [
      [null, '', 'Sáng hôm sau, quả trứng khẽ cựa mình. Bấm A để gõ nhẹ lên vỏ.'],
    ] },

    // ---------- Hồi 1: Làng Ngũ Sắc (Con) ----------
    { id: 'h1-chao', khi: 'room', cap: ['baby'], cau: [
      [null, '', '{pet} chớp chớp mắt nhìn quanh, rồi dụi đầu vào tay bạn.'],
      ['gia-quy', 'cuoi', 'Nở rồi! Chào {pet}, chào mừng con đến Làng Ngũ Sắc.'],
      ['gia-quy', 'cuoi', 'Tinh linh mới nở cũng như em bé: đói thì cho ăn, mệt thì cho ngủ, bẩn thì tắm rửa, dọn dẹp.'],
      ['gia-quy', 'ke-chuyen', 'Nhớ chơi với nó (R2) và vuốt ve nó (X). Tinh linh vui thì mau lớn, lại thương chủ.'],
      ['gia-quy', 'chi-xa', 'Lúc rảnh thì ra bản đồ đi dạo. Trong làng có Trường học, Chợ và Võ đường, ai cũng sẵn lòng giúp cháu.'],
      ['gia-quy', 'gat-dau', 'Thôi, ta về Đài đây. Có gì lạ thì cứ đến tìm ta.'],
    ] },
    { id: 'h1-ban-do', khi: 'map', cap: ['baby', 'child'], cau: [
      ['gia-quy', 'chi-xa', 'Đây là Làng Ngũ Sắc, nằm ngay giữa quần đảo Elemon.'],
      ['gia-quy', 'ke-chuyen', 'Quanh làng có năm vùng đất, mỗi vùng một hệ: Núi lửa, Núi pha lê, Rừng cổ thụ, Hẻm vực và Hồ thác.'],
      ['gia-quy', 'lo-lang', '{pet} còn nhỏ lắm, chưa ra khỏi làng được đâu. Đợi nó lớn thêm chút đã.'],
      ['gia-quy', 'cuoi', 'Giờ thì ghé Trường học đi. Cô Rắn dạy hay lắm.'],
    ] },
    { id: 'h1-truong', khi: 'school', cap: ['baby', 'child'], cau: [
      ['co-ran', 'cuoi', 'Chào trò mới! Cô là cô Rắn. Hôm nay mình học bài đầu tiên: Ngũ Hành.'],
      ['co-ran', 'giang', 'Mọi thứ trên quần đảo đều thuộc một trong năm hệ: Kim, Mộc, Thủy, Hỏa, Thổ. {pet} của trò thuộc hệ {he}.'],
      ['co-ran', 'giang', 'Năm hệ nuôi nhau thành một vòng, gọi là tương sinh: Mộc sinh Hỏa, Hỏa sinh Thổ, Thổ sinh Kim, Kim sinh Thủy, Thủy sinh Mộc.'],
      ['co-ran', 'suy-nghi', 'Nhưng có hệ lại khắc hệ, gọi là tương khắc: Thủy dập Hỏa, Hỏa nung chảy Kim. Khi đấu thì nhớ điều này nhé.'],
      ['co-ran', 'ngac-nhien', 'Mà lạ lắm, mấy hôm nay con suối sau trường cứ đục ngầu. Chắc tại mưa thôi…'],
      ['co-ran', 'khen', 'Thôi, vào học nào!'],
    ] },
    { id: 'h1-cho', khi: 'seedShop', cap: ['baby', 'child'], cau: [
      ['bac-soc', 'chao', 'Ối, khách mới! Bác là Bác Sóc, chuyên bán hạt giống với nông sản cho cả làng.'],
      ['bac-soc', 'dua-hat', 'Bác mách cháu nhé: ăn đồ đúng hệ {he} thì {pet} lên Linh khí nhanh nhất.'],
      ['bac-soc', 'suy-nghi', 'Mà dạo này lạ lắm. Hạt giống mang từ Rừng cổ thụ về, gieo mãi chẳng lên.'],
      ['bac-soc', 'suy-nghi', 'Mấy người buôn từ Núi lửa về còn kể khói trên miệng núi chuyển màu tím. Bán hàng mấy chục năm, bác chưa thấy bao giờ.'],
      ['bac-soc', 'cuoi-lon', 'Thôi, chuyện người lớn để người lớn lo. Cháu xem hàng đi!'],
    ] },
    { id: 'h1-vo-duong', khi: 'voduong', cap: ['baby', 'child'], cau: [
      ['su-phu', 'dung', 'Đệ tử mới hả? Ta là sư phụ của Võ đường này.'],
      ['su-phu', 'cuoi', '{pet} còn nhỏ, nhưng tập từ nhỏ thì lớn lên mới khỏe. Đấm bao cát cho đúng nhịp, rồi lướt tới mà ra đòn.'],
      ['su-phu', 'ngac-nhien', 'Sáng nay ta lên đồi tập, thấy phía Núi lửa bốc khói tím. Năm chục năm luyện võ, ta chưa thấy khói màu ấy.'],
      ['su-phu', 'lay-da', 'Có chuyện gì đó sắp tới. Cứ tập cho chăm vào.'],
    ] },
    { id: 'h1-ket', khi: 'room', cap: ['baby', 'child'], lv: 4, cau: [
      [null, '', 'Chiều hôm ấy, Già Quy chống gậy ghé qua nhà.'],
      ['gia-quy', 'cuoi', '{pet} lớn nhanh quá! Cháu chăm khéo đấy.'],
      ['gia-quy', 'lo-lang', 'Ta vừa đi một vòng làng, ai cũng kể chuyện lạ: cây héo, suối đục, núi lửa bốc khói tím.'],
      ['gia-quy', 'ke-chuyen', 'Chuyện này làm ta nhớ đến một truyền thuyết rất cũ, về Đài Ngũ Hành…'],
      ['gia-quy', 'buon', 'Đợi {pet} lớn thêm chút nữa, ta sẽ kể cháu nghe. Giờ cứ chăm nó cho thật tốt.'],
      [null, '', '{pet} nhìn theo bóng Già Quy, khẽ kêu lên một tiếng.'],
    ] },

    // ---------- Hồi 2: Truyền thuyết (Nhi) ----------
    { id: 'h2-truyen-thuyet', khi: 'room', cap: ['child'], cau: [
      [null, '', 'Tối hôm ấy, Già Quy lại tìm đến. Lần này ông không cười.'],
      ['gia-quy', 'ke-chuyen', '{pet} đã lớn rồi. Đến lúc cháu nghe câu chuyện ta đã hứa.'],
      ['gia-quy', 'ke-chuyen', 'Ngàn năm trước, Hư Ảnh tràn ra từ một khe nứt của đất trời. Nó không thuộc hệ nào, chỉ biết nuốt Linh khí.'],
      ['gia-quy', 'gio-gay', 'Năm Thần thú hộ vùng đã phong ấn nó dưới Đài Ngũ Hành. Từ đó, mỗi Thần thú canh giữ một vùng đất.'],
      ['gia-quy', 'lo-lang', 'Đêm trứng của cháu đến, phong ấn đã nứt. Năm mảnh Hư Ảnh bay về năm vùng, nhập vào chính các Thần thú.'],
      ['gia-quy', 'buon', 'Cây héo, suối đục, núi lửa khói tím… là vì vậy. Những kẻ canh giữ giờ thành thứ phải canh chừng.'],
      ['gia-quy', 'chi-xa', '{vung} là vùng cùng hệ với {pet}. Đường tới đó đã mở. Hãy đi, nhưng chỉ ở phần rìa thôi.'],
      ['gia-quy', 'gio-gay', 'Giải thoát những bóng Hư nhỏ, nhặt những gì còn sót lại. Khi {pet} đủ mạnh, ta sẽ nói cháu biết phải làm gì tiếp.'],
    ] },
    { id: 'h2-ban-do', khi: 'map', cap: ['child'], cau: [
      ['gia-quy', 'chi-xa', '{vung} ở phía kia. Thấy làn khói tím trên đó không? Đó là dấu vết của Hư Ảnh.'],
      ['gia-quy', 'cuoi', 'Mỗi chuyến đi tốn Năng lượng, làm {pet} đói và lấm lem, bị thương còn mất Sức khỏe. Cho nó ăn, tắm, ngủ đủ rồi hẵng đi.'],
    ] },
    { id: 'h2-vung', khi: 'vungdat', cap: ['child'], cau: [
      [null, '', 'Rìa {vung}. Không khí nặng mùi khói, cỏ cây ngả màu xám tro.'],
      [null, '', 'Xa xa, giữa làn khói tím, một bóng khổng lồ khẽ cựa mình. Rồi tất cả lại im lặng.'],
      [null, '', '{pet} dựng lông, gầm gừ thật khẽ. Phía trước, những bóng Hư nhỏ đang lảng vảng.'],
    ] },
    { id: 'h2-vo-duong', khi: 'voduong', cap: ['child'], cau: [
      ['su-phu', 'ngac-nhien', 'Cháu ra rìa {vung} rồi à? Bóng Hư ở đó là tinh linh bị khói tím nhập, không phải quái vật.'],
      ['su-phu', 'dung', 'Đánh để giải thoát chúng, không phải để giết. Khói tan rồi, chúng sẽ trở về với núi rừng.'],
      ['su-phu', 'lay-da', 'Khói tím ra đòn bất ngờ lắm. Thấy đòn tới thì lướt đi mà né (R1), đừng đứng đó chịu trận.'],
    ] },
    { id: 'h2-truong', khi: 'school', cap: ['child'], cau: [
      ['co-ran', 'giang', 'Ra vùng đất thì nhớ bài tương khắc: đánh vào hệ mình khắc thì mạnh gấp rưỡi, gặp hệ khắc mình thì yếu đi.'],
      ['co-ran', 'suy-nghi', 'Còn Hư Ảnh không thuộc hệ nào… nên cũng chẳng hệ nào khắc được nó. Cô nghĩ mãi vẫn chưa ra.'],
    ] },
    { id: 'h2-cho', khi: 'seedShop', cap: ['child'], cau: [
      ['bac-soc', 'suy-nghi', 'Cháu ra vùng đất rồi hả? Cẩn thận đấy. Giờ mấy người buôn chẳng ai dám đi đường {vung} nữa.'],
      ['bac-soc', 'dua-hat', 'Nhớ cho {pet} ăn đúng hệ trước khi đi. Bụng đói thì đánh đấm gì được.'],
    ] },

    // ---------- Cách chơi mới (28/10/2026: chỉ số thống nhất, THIET-KE.md mục 6) ----------
    // mỗi cảnh một mốc level riêng để hiện ở lần ghé sau, không nối liền cảnh cũ cùng chỗ; không giới hạn cấp
    // (người đã qua Hồi 2 vẫn nghe được), riêng Linh khí chỉ khi còn tiến hóa
    { id: 'h2-suc-khoe', khi: 'room', lv: 9, cau: [
      [null, '', 'Già Quy lại ghé qua, ngồi xuống cạnh {pet}.'],
      ['gia-quy', 'lo-lang', 'Cháu để ý thanh Sức khỏe của {pet} chưa? Sức khỏe còn bao nhiêu phần thì ra trận máu cũng chỉ còn bấy nhiêu phần.'],
      ['gia-quy', 'ke-chuyen', 'Ngất đi thì chỉ còn 10, dưới 15 là phải ở nhà. Sức khỏe đã yếu mà còn để nó đói, để nó bẩn là đổ bệnh đấy.'],
      ['gia-quy', 'gat-dau', 'Muốn hồi thì cho nó ngủ, cho ăn đồ hệ Mộc. Ốm, hay Sức khỏe dưới 60, thì vào Vệ sinh lấy thuốc cho uống.'],
    ] },
    { id: 'h2-vo-duong-bai', khi: 'voduong', lv: 8, cau: [
      ['su-phu', 'dung', 'Ở Võ đường này, tập luyện thì lên Sức mạnh, thắng Solo đối kháng thì lên Tinh thần, mỗi thứ một lần một ngày.'],
      ['su-phu', 'lay-da', 'Solo là đấu tay đôi với đối thủ cùng Level. Thắng thì {pet} vui, thua thì buồn, mà trận nào cũng đói, mệt, lấm lem.'],
      ['su-phu', 'that-vong', 'Mệt thì đòn yếu và chậm, đói thì Linh lực hồi chậm, buồn thì khó ra đòn hiểm. Còn {pet} vui hẳn thì đòn mạnh thêm đấy.'],
    ] },
    { id: 'h2-nau-an', khi: 'seedShop', lv: 10, cau: [
      ['bac-soc', 'cuoi-lon', 'Cháu biết nấu ăn chưa? Ở nhà vào Hoạt động, chọn Nấu ăn nè. Nấu khéo thì món được sao, càng nhiều sao càng bổ.'],
      ['bac-soc', 'dua-hat', 'Món Mộc ăn vô là hồi Sức khỏe liền. Món Hỏa thêm Sức mạnh, Thủy thêm Nhanh nhẹn, Thổ thêm Bền bỉ, Kim thêm Thủ.'],
      ['bac-soc', 'suy-nghi', 'Mà mấy món kia chỉ có tác dụng tới hết chuyến đi hay trận Solo kế tiếp, mỗi lần giữ được một món thôi nha.'],
    ] },
    { id: 'h2-linh-khi', khi: 'school', cap: ['child', 'teen'], lv: 12, cau: [
      ['co-ran', 'giang', 'Bài mới: Linh khí. {pet} ăn đồ hệ nào thì Linh khí hệ ấy tăng, mà đã tăng rồi thì không bao giờ mất.'],
      ['co-ran', 'giang', 'Level 20 cần một hệ đạt 30, Level 45 cần hệ cao nhất đạt 60 thì mới tiến hóa. Lên Level, điểm thuộc tính cũng chia theo Linh khí.'],
      ['co-ran', 'suy-nghi', 'Hệ nào cao cũng có cái hay: Kim thêm Thủ, lâu đói; Mộc tự hồi Sức khỏe, ít ốm; Thủy vui lâu, câu cá nấu ăn dễ hơn.'],
      ['co-ran', 'chop-mat', 'Hỏa đánh mạnh nhưng mau đói; Thổ ngủ là hồi Năng lượng nhanh. Trò muốn {pet} giỏi gì thì cho ăn hệ ấy nhé.'],
    ] },
    { id: 'h2-ngoc', khi: 'school', lv: 15, cau: [
      ['co-ran', 'chop-mat', 'Ngọc nhặt ở vùng đất thì gắn ở trang Thuộc tính (SELECT), ngọc hệ nào tăng hai thuộc tính hệ ấy. Ô mở ở Level 6, 15, 21, 46, 100.'],
    ] },

    // ---------- Hồi 3: Vào sâu (Thiếu niên) ----------
    // (lời mới không dùng {he} hay {vung}: câu có chúng phải đọc thành năm bản giọng)
    { id: 'h3-khu-sau', khi: 'room', cap: ['teen'], cau: [
      [null, '', 'Sáng sớm, Già Quy đã đứng chờ trước cửa, cây gậy chống cắm sâu xuống đất.'],
      ['gia-quy', 'ngac-nhien', '{pet} thành Thiếu niên rồi! Nhìn nó xem, mắt sáng, chân vững hẳn ra.'],
      ['gia-quy', 'ke-chuyen', 'Giờ nó đủ sức vào sâu hơn phần rìa. Khói Hư ở khu thứ hai dày hơn, bóng Hư cũng mạnh hơn nhiều.'],
      ['gia-quy', 'lo-lang', 'Ta phải nói thật với cháu. Ở khu sâu nhất mỗi vùng, chính Thần thú canh giữ đang bị Hư Ảnh nhập.'],
      ['gia-quy', 'gio-gay', 'Chưa đến lúc gặp nó đâu. Cứ thanh tẩy từng khu một. Mỗi khu sạch khói, Thần thú lại nhẹ đi một phần.'],
      ['gia-quy', 'gat-dau', 'Đi đi. Nhớ về nhà ăn ngủ cho đủ, đừng để {pet} kiệt sức.'],
    ] },
    { id: 'h3-vo-duong', khi: 'voduong', cap: ['teen'], cau: [
      ['su-phu', 'cuoi', 'Thiếu niên rồi à? Đòn của {pet} đã có lực rồi đấy.'],
      ['su-phu', 'dung', 'Bóng Hư ở khu sâu biết vây đánh. Đừng lao vào giữa bầy, đánh từ rìa vào, hạ từng con một.'],
      ['su-phu', 'lay-da', 'Gặp con đầu đàn chặn lối thì đánh tới cùng. Hạ được nó, lối đi tiếp mới mở.'],
    ] },
    { id: 'h3-truong', khi: 'school', cap: ['teen'], cau: [
      ['co-ran', 'suy-nghi', 'Cô đọc lại sách cổ rồi. Ngày xưa năm Thần thú không đánh Hư Ảnh từng con, mà cùng lúc cả năm.'],
      ['co-ran', 'giang', 'Không hệ nào khắc được nó, nhưng cả năm hệ hợp lại thì khác hẳn. Trò nhớ điều này nhé.'],
    ] },
    { id: 'h3-cho', khi: 'seedShop', cap: ['teen'], cau: [
      ['bac-soc', 'suy-nghi', 'Cháu nghe chưa? Có người thấy một con rồng lửa khổng lồ lượn quanh miệng núi, khói tím quấn đầy mình.'],
      ['bac-soc', 'suy-nghi', 'Chắc là Viêm Long. Ngày xưa nó canh Núi lửa, giờ thì chẳng ai dám bén mảng lên đó nữa.'],
      ['bac-soc', 'dua-hat', 'Đi sâu thì mang nhiều đồ ăn vào. Bụng no mới đánh lâu được.'],
    ] },

    // ---------- Hồi 4: Thần thú (Trưởng thành) ----------
    { id: 'h4-than-thu', khi: 'room', cap: ['adult'], cau: [
      [null, '', 'Đêm ấy, Già Quy mang tới một cuộn da cũ đã ngả màu.'],
      ['gia-quy', 'ke-chuyen', 'Đây là bản đồ ngàn năm trước. Năm chấm sáng là năm Thần thú: Viêm Long, Kim Ưng, Thụ Nhân, Thủy Long và Thổ Long.'],
      ['gia-quy', 'buon', 'Giờ cả năm đều mang khói tím trong người. Chúng không còn nhận ra ai nữa.'],
      ['gia-quy', 'gio-gay', '{pet} đã Trưởng thành. Đến lúc vào khu sâu nhất, đối mặt với Thần thú của vùng nhà.'],
      ['gia-quy', 'chi-xa', 'Đánh để giải thoát, đừng đánh vì căm giận. Thắng rồi, Thần thú sẽ để lại một viên Ngọc Hồn.'],
      ['gia-quy', 'ke-chuyen', 'Thần thú được giải thoát sẽ mở đường sang vùng kế tiếp, theo vòng tương sinh. Gom đủ năm viên thì về tìm ta.'],
    ] },
    { id: 'h4-vo-duong', khi: 'voduong', cap: ['adult'], cau: [
      ['su-phu', 'that-vong', 'Thần thú không phải bóng Hư. Nó đánh mạnh, lại biết đổi đòn. Đứng yên một nhịp là ngã ngay.'],
      ['su-phu', 'dung', 'Lướt né cho khéo, giữ thanh tuyệt chiêu cho lúc nó sơ hở. Đánh trúng một đòn ấy hơn chục đòn thường.'],
    ] },

    // ---------- Gặp và giải thoát Thần thú (cổng vùng đất, game/src/vung-dat.js) ----------
    // vung: vùng của cảnh; man: 'gate' (cổng, mặc định) hoặc 'result' (bảng kết quả sau chuyến đi);
    // dk: 'than-thu' = khu sâu nhất đã mở mà Thần thú chưa được giải thoát, 'da-thoat' = đã giải thoát
    { id: 'tt-hoa-gap', khi: 'vungdat', vung: 'hoa', dk: 'than-thu', cau: [
      [null, '', 'Lối vào khu sâu nhất của Núi lửa. Dung nham chảy thành sông, khói tím cuộn lên che kín bầu trời.'],
      [null, '', 'Trên miệng núi, Viêm Long vươn mình gầm vang. Ngọn lửa của nó giờ cháy một màu tím lạnh.'],
      [null, '', '{pet} ngẩng nhìn lên đỉnh núi, không lùi lấy một bước.'],
    ] },
    { id: 'tt-hoa-thoat', khi: 'vungdat', vung: 'hoa', man: 'result', dk: 'da-thoat', cau: [
      [null, '', 'Khói tím tan dần. Ngọn lửa của Viêm Long đỏ rực trở lại.'],
      [null, '', 'Viêm Long cúi đầu thật thấp trước {pet}, rồi thả xuống một viên ngọc đỏ rực: Ngọc Hồn hệ Hỏa.'],
      [null, '', 'Mảnh khói Hư cuối cùng rời khỏi nó, bay vụt về phía Đài Ngũ Hành giữa làng.'],
    ] },
    { id: 'tt-kim-gap', khi: 'vungdat', vung: 'kim', dk: 'than-thu', cau: [
      [null, '', 'Lối vào khu sâu nhất của Núi pha lê. Những cột pha lê đã đục màu tím, rạn nứt từng mảng.'],
      [null, '', 'Kim Ưng lượn vòng trên cao, đôi cánh bạc phủ kín khói Hư. Tiếng rít của nó làm pha lê rung lên.'],
      [null, '', '{pet} dõi theo bóng cánh ấy, móng bấu chặt xuống nền đá.'],
    ] },
    { id: 'tt-kim-thoat', khi: 'vungdat', vung: 'kim', man: 'result', dk: 'da-thoat', cau: [
      [null, '', 'Đôi cánh Kim Ưng sáng bạc trở lại. Khói Hư rơi xuống như tro tàn.'],
      [null, '', 'Nó đáp xuống trước {pet}, nhả ra một viên ngọc trắng bạc: Ngọc Hồn hệ Kim.'],
      [null, '', 'Mảnh khói Hư cuối cùng rời khỏi nó, bay vụt về phía Đài Ngũ Hành giữa làng.'],
    ] },
    { id: 'tt-moc-gap', khi: 'vungdat', vung: 'moc', dk: 'than-thu', cau: [
      [null, '', 'Lối vào khu sâu nhất của Rừng cổ thụ. Cây cối khô héo, rễ cây quằn quại như đang đau.'],
      [null, '', 'Giữa rừng, Thụ Nhân chậm rãi đứng dậy. Từng nhánh cành trên người nó rỉ ra khói tím.'],
      [null, '', '{pet} hít một hơi thật sâu, rồi bước tới.'],
    ] },
    { id: 'tt-moc-thoat', khi: 'vungdat', vung: 'moc', man: 'result', dk: 'da-thoat', cau: [
      [null, '', 'Lá non bật ra trên những nhánh cành khô. Thụ Nhân đã tỉnh lại.'],
      [null, '', 'Nó chìa bàn tay gỗ, đặt trước mặt {pet} một viên ngọc xanh lá: Ngọc Hồn hệ Mộc.'],
      [null, '', 'Mảnh khói Hư cuối cùng rời khỏi nó, bay vụt về phía Đài Ngũ Hành giữa làng.'],
    ] },
    { id: 'tt-thuy-gap', khi: 'vungdat', vung: 'thuy', dk: 'than-thu', cau: [
      [null, '', 'Lối vào khu sâu nhất của Hồ thác. Nước hồ đen đặc, thác đổ xuống mà không một tiếng động.'],
      [null, '', 'Mặt hồ dậy sóng. Thủy Long trồi lên, đôi mắt sáng một màu tím lạnh lẽo.'],
      [null, '', '{pet} đứng vững trên bờ đá, chờ nó lao tới.'],
    ] },
    { id: 'tt-thuy-thoat', khi: 'vungdat', vung: 'thuy', man: 'result', dk: 'da-thoat', cau: [
      [null, '', 'Nước hồ trong vắt trở lại, tiếng thác đổ vang lên rộn ràng.'],
      [null, '', 'Thủy Long khẽ chạm mũi vào {pet}, để lại một viên ngọc xanh biếc: Ngọc Hồn hệ Thủy.'],
      [null, '', 'Mảnh khói Hư cuối cùng rời khỏi nó, bay vụt về phía Đài Ngũ Hành giữa làng.'],
    ] },
    { id: 'tt-tho-gap', khi: 'vungdat', vung: 'tho', dk: 'than-thu', cau: [
      [null, '', 'Lối vào khu sâu nhất của Hẻm vực. Vách đá nứt toác, bụi đất bay mù mịt trong khói tím.'],
      [null, '', 'Mặt đất rung chuyển. Thổ Long trườn ra từ lòng vực, vảy đá cọ vào nhau ken két.'],
      [null, '', '{pet} trụ chân thật vững, sẵn sàng cho trận đánh lớn nhất từ trước tới giờ.'],
    ] },
    { id: 'tt-tho-thoat', khi: 'vungdat', vung: 'tho', man: 'result', dk: 'da-thoat', cau: [
      [null, '', 'Bụi đất lắng xuống. Vảy đá của Thổ Long sáng lên một màu vàng ấm.'],
      [null, '', 'Thổ Long cúi đầu, đẩy tới chân {pet} một viên ngọc vàng đất: Ngọc Hồn hệ Thổ.'],
      [null, '', 'Mảnh khói Hư cuối cùng rời khỏi nó, bay vụt về phía Đài Ngũ Hành giữa làng.'],
    ] },

    // ---------- Hồi 5: Năm Ngọc Hồn ----------
    { id: 'h5-huyen-thoai', khi: 'room', cap: ['legend'], cau: [
      [null, '', '{pet} vừa tiến hóa lần cuối. Ánh sáng tỏa ra khắp căn nhà nhỏ.'],
      ['gia-quy', 'ngac-nhien', 'Huyền thoại… Cả đời ta mới thấy một tinh linh đi tới bậc này.'],
      ['gia-quy', 'ke-chuyen', 'Hồi ta còn trẻ, người ta bảo chỉ Thần thú mới mạnh được như vậy. Giờ {pet} đứng ngang hàng với họ rồi.'],
      ['gia-quy', 'gat-dau', 'Cứ đi tiếp con đường của cháu. Ta tin hai đứa.'],
    ] },
    // dk 'du-ngoc': đủ 5 Ngọc Hồn mà chưa thắng Hư Ảnh
    { id: 'h5-du-ngoc', khi: 'room', dk: 'du-ngoc', cau: [
      [null, '', 'Năm viên Ngọc Hồn nằm cạnh nhau trên bàn, sáng lên năm màu: đỏ, bạc, xanh lá, xanh dương và vàng đất.'],
      ['gia-quy', 'ngac-nhien', 'Đủ cả năm viên rồi sao? Ta nghe chúng ngân lên từ tận đầu làng.'],
      ['gia-quy', 'lo-lang', 'Nhưng cháu phải biết điều này. Đặt năm viên lên năm trụ, phong ấn sẽ mở, và Hư Ảnh sẽ hiện nguyên hình.'],
      ['gia-quy', 'gio-gay', 'Không còn cách nào khác. Năm mảnh của nó đã dồn về dưới Đài, chỉ chờ ngày phá phong ấn mà ra.'],
      ['gia-quy', 'chi-xa', 'Khi nào sẵn sàng, hãy đến Đài Ngũ Hành giữa làng. Ta sẽ chờ ở đó.'],
    ] },
    { id: 'h5-ban-do', khi: 'map', dk: 'du-ngoc', cau: [
      ['gia-quy', 'chi-xa', 'Đài Ngũ Hành ở ngay giữa làng, giữa Trường học và Võ đường. Năm trụ đá đang chờ năm viên ngọc.'],
    ] },

    // ---------- Hồi cuối: Đài Ngũ Hành (trong phim 'dai-mo' và 'dai-ket') ----------
    { id: 'dai-truoc', khi: 'phim', cau: [
      ['gia-quy', 'lo-lang', 'Cháu đến rồi. Năm trụ đá đã sáng cả, chúng biết Ngọc Hồn đã về.'],
      ['gia-quy', 'ke-chuyen', 'Ngàn năm trước, năm Thần thú cùng đứng quanh Đài này. Hôm nay chỉ có cháu và {pet}.'],
      ['gia-quy', 'gio-gay', 'Nhưng hai đứa không đơn độc. Năm Thần thú cháu đã giải thoát sẽ đứng sau lưng hai đứa.'],
      ['gia-quy', 'gat-dau', 'Đặt ngọc đi. Dù chuyện gì xảy ra, đừng lùi bước.'],
    ] },
    { id: 'dai-sau', khi: 'phim', cau: [
      ['gia-quy', 'cuoi', 'Xong rồi… Thật sự xong rồi.'],
      ['gia-quy', 'ke-chuyen', 'Ngàn năm trước phải cần tới năm Thần thú. Hôm nay, một đứa trẻ và {pet} đã làm được điều ấy.'],
      ['gia-quy', 'gat-dau', 'Phong ấn mới giữ bằng sức của cả năm hệ, sẽ bền hơn phong ấn cũ rất nhiều.'],
      ['gia-quy', 'chi-xa', 'Hư Ảnh vẫn nằm dưới Đài. Muốn so tài với nó thì đến Võ đường, Sư phụ sẽ sắp trận cho.'],
      ['gia-quy', 'cuoi', 'Giờ thì về nhà nghỉ ngơi đi. Cả làng đang chờ mừng hai đứa đấy.'],
    ] },
    // dk 'thang-hu': đã thắng Hư Ảnh
    { id: 'ket-truong', khi: 'school', dk: 'thang-hu', cau: [
      ['co-ran', 'khen', 'Trò làm được rồi! Năm hệ hợp lại, đúng như sách cổ viết.'],
      ['co-ran', 'chop-mat', 'Từ nay bài Ngũ Hành của cô có thêm một chương mới, chương về {pet}.'],
    ] },
    { id: 'ket-cho', khi: 'seedShop', dk: 'thang-hu', cau: [
      ['bac-soc', 'cuoi-lon', 'Hạt giống từ Rừng cổ thụ lên xanh mướt rồi! Người buôn lại đi đầy đường.'],
      ['bac-soc', 'cam-on', 'Cả làng nợ cháu với {pet} một bữa tiệc. Phần hạt giống để bác lo!'],
    ] },
    { id: 'ket-vo-duong', khi: 'voduong', dk: 'thang-hu', cau: [
      ['su-phu', 'cuoi', 'Ta nghe hết rồi. Đệ tử của ta đã đánh bại Hư Ảnh.'],
      ['su-phu', 'dung', 'Giờ nó là một đối thủ ở Võ đường này. Muốn thử sức thì cứ vào, nhưng đừng mong nó nương tay.'],
    ] },
  ],
};
