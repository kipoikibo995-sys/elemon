// Elemon: môn Xã hội at the Trường học, in place of Học Hệ (the user, 03/11/2026: "thêm một bộ môn là xã hội ...
// phù hợp cho trẻ nhỏ và người lớn ... nó sẽ thay thế môn học các hệ"; "tao muốn câu ngẫu nhiên đi, vì người lớn và
// trẻ nhỏ đều chơi mà").
// The demo's school is not edited: its third card is renamed and makeQ answers subject 2 from the bank below
// (5 questions a lesson, none twice in one lesson, easy and hard mixed, the answers shuffled).
// After each answer cô Rắn says why (the bank's third field) on a strip under the answers, until A: the demo's own
// 1.3 s step to the next question waits for it. Long answers are drawn smaller so they stay inside their button.
// The card picture is still the_he's until a Xã hội card is drawn (th_the_xa-hoi, used when it is there).
// The bank: one row a question, [question, [right answer, 3 wrong ones], why]; the draft the user approved is
// xa-hoi-cau-hoi.md (Mimo-0.1).
(() => {
  if (typeof makeQ !== 'function' || typeof drawSchool !== 'function' || typeof schoolInput !== 'function' ||
      typeof SUBJECTS === 'undefined') return;
  const SUBJ = 2, BTN_W = 126, MIN_PX = 12, WAIT = 1300;
  const BANK = [
    ["Đèn đỏ bật thì phải làm gì?", ["Dừng lại", "Đi nhanh qua", "Bấm còi", "Rẽ phải ngay"], "Đèn đỏ là phải dừng, chờ đèn xanh mới đi."],
    ["Đèn vàng nghĩa là gì?", ["Chậm lại, dừng", "Đi nhanh hơn", "Được quay đầu", "Đường vắng xe"], "Đèn vàng báo sắp chuyển đỏ, phải giảm tốc và dừng trước vạch."],
    ["Đi bộ qua đường ở đâu là an toàn?", ["Vạch kẻ đường", "Giữa ngã tư", "Sau xe buýt", "Chỗ nào gần nhất"], "Vạch kẻ trắng là lối dành cho người đi bộ."],
    ["Đi bộ trên đường phố nên đi ở đâu?", ["Vỉa hè", "Giữa lòng đường", "Làn xe máy", "Dải phân cách"], "Vỉa hè dành cho người đi bộ, tránh xa xe cộ."],
    ["Ngồi sau xe máy phải đội gì?", ["Mũ bảo hiểm", "Mũ len", "Nón lá", "Không cần đội"], "Mũ bảo hiểm bảo vệ đầu khi chẳng may ngã xe."],
    ["Ở Việt Nam, xe cộ đi bên nào của đường?", ["Bên phải", "Bên trái", "Ở giữa", "Bên nào cũng được"], "Việt Nam đi bên phải, nhiều nước như Nhật, Anh đi bên trái."],
    ["Biển báo tròn, viền đỏ thường là biển gì?", ["Biển cấm", "Biển chỉ dẫn", "Biển quảng cáo", "Biển tên đường"], "Biển tròn viền đỏ báo điều bị cấm, ví dụ cấm rẽ, cấm đỗ."],
    ["Biển tam giác viền đỏ nền vàng là biển gì?", ["Biển nguy hiểm", "Biển cấm", "Biển hiệu lệnh", "Biển tên phố"], "Biển tam giác cảnh báo phía trước có nguy hiểm."],
    ["Biển tròn nền xanh dương là biển gì?", ["Biển hiệu lệnh", "Biển cấm", "Biển nguy hiểm", "Biển quảng cáo"], "Biển tròn nền xanh bắt buộc phải làm theo, ví dụ đi thẳng."],
    ["Nghe còi xe cứu thương phía sau thì nên?", ["Nhường đường", "Chạy đua theo", "Dừng giữa đường", "Bấm còi lại"], "Xe cứu thương đang chở người cần cứu gấp, phải nhường đường."],
    ["Trẻ nhỏ ngồi ô tô an toàn nhất ở đâu?", ["Ghế sau, thắt dây", "Ghế trước", "Trong lòng mẹ", "Thò đầu ra cửa"], "Ghế sau có dây an toàn hoặc ghế trẻ em là chỗ an toàn nhất."],
    ["Đã uống rượu bia thì có được lái xe không?", ["Không được", "Được nếu ít", "Được ban ngày", "Được nếu đi chậm"], "Đã uống rượu bia là không lái xe, dù chỉ một chút."],
    ["Đang lái xe máy có được nghe điện thoại cầm tay?", ["Không được", "Được nếu nói ngắn", "Được ở đường vắng", "Được ban đêm"], "Vừa lái vừa cầm điện thoại rất dễ gây tai nạn."],
    ["Đi xe đạp điện có phải đội mũ bảo hiểm không?", ["Có", "Không", "Chỉ khi trời mưa", "Chỉ người lớn"], "Đi xe đạp điện, xe máy điện đều phải đội mũ bảo hiểm."],
    ["Chơi đùa ở đâu là an toàn?", ["Sân chơi, công viên", "Lòng đường", "Đường tàu", "Bãi đỗ xe"], "Lòng đường và đường tàu rất nguy hiểm, không được chơi ở đó."],
    ["Xuống xe buýt rồi muốn qua đường thì?", ["Chờ xe buýt đi hẳn", "Chạy trước đầu xe", "Chui sau xe", "Chạy vòng qua xe"], "Xe buýt che mất tầm nhìn, chờ xe đi rồi mới qua đường."],
    ["Gặp người lớn tuổi thì nên làm gì?", ["Chào hỏi lễ phép", "Làm ngơ", "Chạy đi chỗ khác", "Chỉ vẫy tay"], "Chào hỏi lễ phép thể hiện mình là người ngoan."],
    ["Được tặng quà thì nên nói gì?", ["Cảm ơn", "Xin lỗi", "Tạm biệt", "Không nói gì"], "Nói cảm ơn khi được giúp đỡ hay được tặng quà."],
    ["Làm vỡ đồ của bạn thì nên nói gì?", ["Xin lỗi", "Cảm ơn", "Kệ nó", "Đổ cho người khác"], "Làm sai thì xin lỗi và tìm cách sửa lỗi."],
    ["Nhận đồ từ người lớn thì nên nhận thế nào?", ["Bằng hai tay", "Bằng một tay", "Giật lấy", "Bằng chân"], "Đưa và nhận bằng hai tay là lễ phép."],
    ["Trước bữa cơm, con nên làm gì?", ["Mời ông bà, bố mẹ", "Ăn trước luôn", "Xem điện thoại", "Bỏ đi chơi"], "Mời cả nhà trước khi ăn là nét đẹp của người Việt."],
    ["Mua hàng đông người thì nên?", ["Xếp hàng chờ lượt", "Chen lên trước", "Đứng ngang hàng", "Hét to gọi"], "Xếp hàng là công bằng và văn minh."],
    ["Trong thư viện thì phải làm gì?", ["Giữ trật tự", "Nói chuyện to", "Chạy nhảy", "Ăn uống thoải mái"], "Thư viện là nơi đọc sách, cần yên lặng."],
    ["Muốn mượn đồ của bạn thì nên?", ["Hỏi trước", "Lấy luôn", "Giấu đi", "Đổi đồ khác"], "Hỏi trước khi mượn và nhớ trả lại."],
    ["Nhặt được ví rơi thì nên làm gì?", ["Trả lại người mất", "Giữ lấy", "Vứt đi", "Lấy tiền ra"], "Nhặt được của rơi trả lại người mất, hoặc nhờ công an."],
    ["Người khác đang nói mà mình chen ngang là?", ["Bất lịch sự", "Rất thông minh", "Bình thường", "Đáng khen"], "Nên chờ người khác nói xong rồi mới nói."],
    ["Lên xe buýt nên nhường ghế cho ai?", ["Người già, bà bầu", "Bạn cùng lớp", "Người khỏe mạnh", "Không ai cả"], "Nhường ghế cho người già, phụ nữ mang thai và trẻ nhỏ."],
    ["Thấy bạn bị ngã thì nên làm gì?", ["Đỡ bạn dậy", "Cười chê bạn", "Bỏ đi", "Quay video"], "Giúp đỡ bạn khi bạn gặp khó khăn."],
    ["Thấy bạn bị bắt nạt thì nên?", ["Báo thầy cô", "Đứng xem", "Bắt nạt theo", "Giả vờ không thấy"], "Báo người lớn để bảo vệ bạn và chính mình."],
    ["Khi ho hoặc hắt hơi nên?", ["Che miệng lại", "Hướng vào bạn", "Hắt thật to", "Không cần che"], "Che miệng để không lây bệnh cho người khác."],
    ["Đi học muộn thì nên làm gì?", ["Xin phép cô giáo", "Lẻn vào chỗ", "Đứng ngoài cửa", "Về nhà luôn"], "Xin phép trước khi vào lớp là lễ phép."],
    ["Đến nhà người khác chơi thì nên?", ["Chào cả nhà", "Mở tủ lạnh", "Chạy khắp nhà", "Lục đồ đạc"], "Chào hỏi chủ nhà và không tự ý đụng đồ."],
    ["Bố của bố gọi là gì?", ["Ông nội", "Ông ngoại", "Bác", "Chú"], "Bên bố là nội, bên mẹ là ngoại."],
    ["Mẹ của mẹ gọi là gì?", ["Bà ngoại", "Bà nội", "Cô", "Dì"], "Bên mẹ là ngoại, bên bố là nội."],
    ["Em trai của bố gọi là gì?", ["Chú", "Cậu", "Bác", "Dượng"], "Em trai của bố là chú, anh trai của bố là bác."],
    ["Anh em trai của mẹ gọi là gì?", ["Cậu", "Chú", "Bác", "Thím"], "Anh em trai của mẹ đều gọi là cậu."],
    ["Em gái của bố gọi là gì?", ["Cô", "Dì", "Mợ", "Thím"], "Chị em gái của bố là cô (miền Trung có nơi gọi là o)."],
    ["Ai chữa bệnh cho mọi người?", ["Bác sĩ", "Thợ may", "Đầu bếp", "Phi công"], "Bác sĩ khám và chữa bệnh ở bệnh viện."],
    ["Ai dập lửa khi có cháy?", ["Lính cứu hỏa", "Bưu tá", "Ca sĩ", "Thợ cắt tóc"], "Lính cứu hỏa dập lửa và cứu người khi có cháy."],
    ["Ai dạy học ở trường?", ["Giáo viên", "Bác sĩ", "Nông dân", "Tài xế"], "Thầy cô giáo dạy chữ và dạy làm người."],
    ["Người lái máy bay gọi là gì?", ["Phi công", "Thủy thủ", "Tài xế", "Thợ máy"], "Phi công lái máy bay, thủy thủ làm việc trên tàu biển."],
    ["Nông dân làm việc chủ yếu ở đâu?", ["Cánh đồng", "Bệnh viện", "Ngân hàng", "Rạp chiếu phim"], "Nông dân trồng lúa, trồng rau trên cánh đồng."],
    ["Ngư dân làm nghề gì?", ["Đánh bắt cá", "Trồng lúa", "Xây nhà", "Dạy học"], "Ngư dân ra biển, ra sông đánh bắt cá."],
    ["Ai thiết kế nhà cửa, công trình?", ["Kiến trúc sư", "Đầu bếp", "Ca sĩ", "Thợ may"], "Kiến trúc sư vẽ thiết kế, thợ xây dựng nên ngôi nhà."],
    ["Hạt gạo lấy từ cây gì?", ["Cây lúa", "Cây ngô", "Cây mía", "Cây dừa"], "Lúa chín, phơi khô, xay xát thành gạo."],
    ["Bưu tá làm công việc gì?", ["Đưa thư, bưu phẩm", "Nấu ăn", "Bán thuốc", "Lái tàu"], "Bưu tá mang thư và bưu phẩm đến từng nhà."],
    ["Gọi cứu hỏa thì bấm số nào?", ["114", "113", "115", "116"], "113 công an, 114 cứu hỏa, 115 cấp cứu."],
    ["Gọi cấp cứu y tế thì bấm số nào?", ["115", "113", "114", "118"], "115 là số cấp cứu y tế."],
    ["Gọi công an thì bấm số nào?", ["113", "114", "115", "112"], "113 là số của công an."],
    ["Người lạ cho kẹo rồi rủ đi chơi thì?", ["Từ chối, báo bố mẹ", "Đi theo luôn", "Nhận kẹo rồi đi", "Giữ bí mật"], "Không đi theo người lạ, kể ngay cho người lớn."],
    ["Bị lạc bố mẹ ở chỗ đông người thì nên?", ["Nhờ chú công an", "Chạy lung tung", "Đi theo người lạ", "Ra đường lớn"], "Đứng yên hoặc nhờ công an, nhân viên ở đó giúp."],
    ["Vì sao không được chọc tay vào ổ điện?", ["Bị điện giật", "Ổ điện bẩn", "Làm hỏng ổ", "Bố mẹ mắng"], "Điện giật rất nguy hiểm, có thể chết người."],
    ["Đi bơi ở sông, hồ thì cần?", ["Có người lớn đi cùng", "Đi một mình", "Đi lúc trời tối", "Bơi thật xa"], "Trẻ em chỉ bơi khi có người lớn trông."],
    ["Có cháy, khói nhiều thì nên di chuyển thế nào?", ["Bò thấp, che mũi", "Đứng thẳng chạy", "Trốn trong tủ", "Đi thang máy"], "Khói bốc lên cao, bò sát sàn để thở được không khí sạch."],
    ["Khi có cháy trong tòa nhà thì đi bằng gì?", ["Cầu thang bộ", "Thang máy", "Nhảy cửa sổ", "Đứng chờ"], "Thang máy có thể mất điện và kẹt khi cháy."],
    ["Ngửi thấy mùi gas trong bếp thì?", ["Mở cửa, không bật điện", "Bật quạt ngay", "Bật lửa xem", "Bật đèn lên"], "Tia lửa điện có thể làm gas phát nổ."],
    ["Thấy người bị điện giật, việc đầu tiên là?", ["Ngắt nguồn điện", "Kéo tay người đó", "Tạt nước vào", "Chạy đi"], "Chạm vào người đang bị giật thì mình cũng bị giật."],
    ["Bị bỏng nhẹ thì nên làm gì?", ["Xả nước mát", "Bôi kem đánh răng", "Bôi nước mắm", "Chọc vỡ bọng"], "Xả nước mát 15–20 phút giúp đỡ đau, không bôi linh tinh."],
    ["Bị chảy máu cam thì nên?", ["Cúi đầu, bóp mũi", "Ngửa đầu ra sau", "Nằm ngửa", "Chạy nhảy"], "Hơi cúi người, bóp phần mềm của mũi khoảng 10 phút."],
    ["Có động đất khi đang ở trong nhà thì nên?", ["Núp dưới gầm bàn", "Đứng cạnh cửa kính", "Đi thang máy", "Ra ban công"], "Núp dưới bàn chắc chắn, tránh xa kính và đồ dễ đổ."],
    ["Trời có bão lớn thì nên?", ["Ở trong nhà", "Ra biển xem sóng", "Đi câu cá", "Trèo lên cây"], "Bão rất nguy hiểm, ở trong nhà chắc chắn cho an toàn."],
    ["Thấy dây điện đứt rơi xuống vũng nước thì?", ["Tránh xa ngay", "Nhặt lên", "Lội qua", "Lấy que khều"], "Nước dẫn điện, đến gần có thể bị điện giật."],
    ["Bình chữa cháy dùng khi nào?", ["Đám cháy nhỏ", "Đám cháy rất lớn", "Để trang trí", "Khi trời nóng"], "Cháy lớn thì thoát ra ngoài và gọi 114."],
    ["Có người gọi điện xin mã OTP của mình thì?", ["Không đưa", "Đưa ngay", "Đưa nếu họ lịch sự", "Đọc một nửa"], "Mã OTP như chìa khoá tài khoản, không đưa cho ai."],
    ["Tin nhắn báo trúng thưởng nhưng phải chuyển tiền trước là?", ["Lừa đảo", "Quà thật", "Khuyến mãi", "Ngân hàng tặng"], "Quà thật không bao giờ bắt mình chuyển tiền trước."],
    ["Mật khẩu nào an toàn hơn?", ["Dài, có chữ và số", "123456", "Ngày sinh của mình", "Tên của mình"], "Mật khẩu dài, khó đoán thì kẻ gian khó mở."],
    ["Không nên đăng gì lên mạng xã hội?", ["Địa chỉ nhà mình", "Ảnh phong cảnh", "Món ăn ngon", "Bức vẽ đẹp"], "Kẻ xấu có thể dùng địa chỉ và thông tin riêng để làm hại mình."],
    ["Bị bắt nạt trên mạng thì nên?", ["Kể với người lớn", "Chửi lại", "Giấu kín", "Chia sẻ khắp nơi"], "Kể cho bố mẹ, thầy cô để được giúp đỡ."],
    ["Bạn mới quen trên mạng hẹn gặp riêng thì?", ["Hỏi ý bố mẹ", "Đi một mình", "Giữ bí mật", "Đi lúc tối"], "Người trên mạng có thể không như mình nghĩ."],
    ["Đường link lạ gửi qua tin nhắn thì?", ["Không bấm vào", "Bấm thử xem", "Gửi cho bạn bè", "Nhập mật khẩu vào"], "Link lạ có thể là bẫy lấy cắp tài khoản."],
    ["Tiết kiệm tiền nghĩa là gì?", ["Để dành một phần", "Tiêu hết ngay", "Mua thật nhiều", "Cho hết người khác"], "Để dành một ít mỗi lần, lâu dần sẽ thành nhiều."],
    ["Tiền Việt Nam có đơn vị là gì?", ["Đồng", "Đô la", "Yên", "Bảng"], "Tiền Việt Nam là đồng, viết tắt là VND."],
    ["Gửi tiền tiết kiệm ở ngân hàng thì được thêm?", ["Tiền lãi", "Tiền phạt", "Quà sinh nhật", "Không được gì"], "Ngân hàng trả lãi cho khoản tiền mình gửi."],
    ["Nhận hàng mua trên mạng thì nên?", ["Kiểm tra hàng", "Vứt hộp ngay", "Không cần xem", "Trả tiền gấp đôi"], "Kiểm tra hàng đúng như đã đặt rồi mới trả tiền nếu được."],
    ["Trước khi mua một món đồ, nên tự hỏi?", ["Mình có cần không", "Bạn có chưa", "Có màu đỏ không", "Có to không"], "Mua thứ mình cần, đừng mua chỉ vì thích nhất thời."],
    ["Nên rửa tay trước khi làm gì?", ["Ăn cơm", "Ngủ trưa", "Xem tivi", "Đọc truyện"], "Rửa tay bằng xà phòng trước khi ăn để không bị đau bụng."],
    ["Mỗi ngày nên đánh răng ít nhất mấy lần?", ["2 lần", "1 tuần 1 lần", "Không cần", "1 tháng 1 lần"], "Đánh răng sáng và tối để răng chắc khỏe."],
    ["Rau xanh cung cấp cho cơ thể chất gì?", ["Vitamin, chất xơ", "Nhiều đường", "Nhiều dầu mỡ", "Chất tạo màu"], "Ăn rau giúp tiêu hoá tốt và khỏe mạnh."],
    ["Nên hạn chế loại đồ ăn nào?", ["Đồ ngọt, đồ chiên", "Rau xanh", "Hoa quả", "Cá"], "Ăn nhiều đồ ngọt, đồ chiên dễ béo phì, sâu răng."],
    ["Tập thể dục đều đặn giúp gì?", ["Cơ thể khỏe mạnh", "Dễ ốm hơn", "Mệt hơn", "Không giúp gì"], "Vận động mỗi ngày giúp xương chắc, tim khỏe."],
    ["Hút thuốc lá gây hại nhiều nhất cho?", ["Phổi", "Tóc", "Móng tay", "Lông mày"], "Khói thuốc làm hại phổi của cả người hút và người hít phải."],
    ["Người lớn mỗi ngày nên uống khoảng bao nhiêu nước?", ["1,5–2 lít", "1 cốc", "10 lít", "Không cần uống"], "Uống đủ nước giúp cơ thể làm việc tốt."],
    ["Trẻ em tiểu học nên ngủ khoảng bao lâu mỗi đêm?", ["9–11 tiếng", "3 tiếng", "5 tiếng", "15 tiếng"], "Ngủ đủ giúp trẻ lớn nhanh và học tốt."],
    ["Xem điện thoại quá lâu dễ bị gì?", ["Hại mắt", "Cao lớn hơn", "Mắt sáng hơn", "Không sao cả"], "Cứ 20 phút nên nhìn ra xa để mắt nghỉ."],
    ["Rác thì bỏ vào đâu?", ["Thùng rác", "Dưới gầm bàn", "Xuống sông", "Ra đường"], "Bỏ rác đúng chỗ để môi trường sạch đẹp."],
    ["Vỏ chai nhựa thuộc loại rác nào?", ["Rác tái chế", "Rác hữu cơ", "Rác nguy hại", "Không phải rác"], "Chai nhựa có thể tái chế thành đồ dùng mới."],
    ["Vỏ chuối thuộc loại rác nào?", ["Rác hữu cơ", "Rác tái chế", "Rác nguy hại", "Rác điện tử"], "Rác hữu cơ có thể ủ làm phân bón cho cây."],
    ["Pin cũ thuộc loại rác nào?", ["Rác nguy hại", "Rác hữu cơ", "Rác tái chế", "Rác thường"], "Pin chứa chất độc, cần bỏ đúng nơi thu gom."],
    ["Đánh răng thì nên làm gì để tiết kiệm nước?", ["Khóa vòi lại", "Để vòi chảy", "Mở vòi to", "Dùng hai vòi"], "Khóa vòi khi chải răng tiết kiệm được rất nhiều nước."],
    ["Trồng nhiều cây xanh giúp gì?", ["Không khí trong lành", "Nóng hơn", "Nhiều bụi hơn", "Ồn ào hơn"], "Cây hút khí CO2 và nhả ra khí oxy cho chúng ta thở."],
    ["Đi chợ nên dùng gì thay túi ni lông?", ["Túi vải", "Thêm túi ni lông", "Túi giấy bóng", "Hộp xốp"], "Túi ni lông cần hàng trăm năm mới phân hủy hết."],
    ["Phá rừng có thể gây ra điều gì?", ["Lũ lụt, sạt lở", "Mưa đúng lúc", "Đất tốt hơn", "Không sao cả"], "Rễ cây giữ đất và nước, mất rừng dễ lũ quét."],
    ["Năng lượng nào là năng lượng sạch?", ["Mặt trời", "Than đá", "Dầu mỏ", "Đốt rác"], "Điện mặt trời, điện gió không thải khói bụi."],
    ["Trái Đất nóng lên chủ yếu do loại khí nào tăng?", ["Khí nhà kính (CO2)", "Khí oxy", "Hơi nước tinh khiết", "Khí heli"], "Đốt than, xăng dầu thải nhiều CO2 giữ nhiệt quanh Trái Đất."],
    ["\"Giờ Trái Đất\" mọi người cùng làm gì?", ["Tắt đèn điện", "Bật hết đèn", "Đốt pháo", "Đi xe máy"], "Tắt đèn một giờ để nhắc nhau tiết kiệm năng lượng."],
    ["Thủ đô của Việt Nam là?", ["Hà Nội", "Huế", "Đà Nẵng", "Cần Thơ"], "Hà Nội là thủ đô, xưa có tên là Thăng Long."],
    ["Thành phố đông dân nhất Việt Nam là?", ["TP. Hồ Chí Minh", "Hà Nội", "Hải Phòng", "Đà Nẵng"], "TP. Hồ Chí Minh là thành phố lớn và đông dân nhất."],
    ["Quốc kỳ Việt Nam là?", ["Cờ đỏ sao vàng", "Cờ xanh sao trắng", "Cờ vàng sao đỏ", "Cờ trắng sao xanh"], "Nền đỏ, giữa là ngôi sao vàng năm cánh."],
    ["Ngày Quốc khánh Việt Nam là ngày nào?", ["2/9", "1/6", "20/11", "8/3"], "Ngày 2/9/1945, nước Việt Nam Dân chủ Cộng hòa ra đời."],
    ["Việt Nam có bao nhiêu dân tộc?", ["54", "10", "30", "100"], "Việt Nam có 54 dân tộc anh em cùng sinh sống."],
    ["Núi nào cao nhất Việt Nam?", ["Fansipan", "Bà Đen", "Ngự Bình", "Tam Đảo"], "Fansipan cao hơn 3.100 m, được gọi là nóc nhà Đông Dương."],
    ["Sông nào chảy qua Hà Nội?", ["Sông Hồng", "Sông Hương", "Sông Hàn", "Sông Sài Gòn"], "Sông Hồng nhiều phù sa nên nước có màu đỏ nâu."],
    ["Vịnh Hạ Long nổi tiếng với gì?", ["Hàng nghìn đảo đá", "Sa mạc cát", "Núi lửa", "Băng tuyết"], "Hạ Long là di sản thiên nhiên thế giới với gần 2.000 hòn đảo."],
    ["Đồng bằng lớn nhất Việt Nam là?", ["Sông Cửu Long", "Sông Hồng", "Sông Mã", "Sông Đà"], "Đồng bằng sông Cửu Long là vựa lúa lớn nhất cả nước."],
    ["Cố đô của nhà Nguyễn là thành phố nào?", ["Huế", "Hà Nội", "Hội An", "Vinh"], "Huế là kinh đô của triều Nguyễn, có Đại Nội nổi tiếng."],
    ["Văn Miếu – Quốc Tử Giám được coi là?", ["Đại học đầu tiên", "Chợ lớn nhất", "Bến cảng", "Cung điện vua"], "Quốc Tử Giám mở năm 1076 ở Thăng Long."],
    ["Ai đánh tan quân Nam Hán trên sông Bạch Đằng năm 938?", ["Ngô Quyền", "Lê Lợi", "Quang Trung", "Lý Thường Kiệt"], "Ngô Quyền cắm cọc gỗ dưới lòng sông để đánh giặc."],
    ["Ai ba lần lãnh đạo đánh thắng quân Nguyên Mông?", ["Trần Hưng Đạo", "Ngô Quyền", "Lê Lợi", "Lý Công Uẩn"], "Nhà Trần ba lần thắng quân Nguyên Mông, Trần Hưng Đạo là vị tướng lớn."],
    ["Vua nào dời đô về Thăng Long năm 1010?", ["Lý Thái Tổ", "Lê Thái Tổ", "Trần Nhân Tông", "Gia Long"], "Lý Công Uẩn (Lý Thái Tổ) viết Chiếu dời đô."],
    ["Vua Quang Trung tên thật là gì?", ["Nguyễn Huệ", "Nguyễn Ánh", "Lê Lợi", "Trần Quốc Tuấn"], "Nguyễn Huệ đại phá quân Thanh vào Tết năm 1789."],
    ["Theo truyền thuyết, rùa vàng đòi lại gươm báu ở hồ nào?", ["Hồ Hoàn Kiếm", "Hồ Tây", "Hồ Ba Bể", "Hồ Xuân Hương"], "Vua Lê Lợi trả gươm cho rùa thần, hồ có tên Hoàn Kiếm."],
    ["Hai Bà Trưng là ai?", ["Hai nữ anh hùng", "Hai nàng tiên", "Hai ca sĩ", "Hai nhà thơ"], "Hai Bà Trưng khởi nghĩa đánh quân Hán năm 40."],
    ["Thánh Gióng cưỡi ngựa sắt đánh giặc nào?", ["Giặc Ân", "Giặc Minh", "Giặc Thanh", "Giặc Nguyên"], "Thánh Gióng là truyền thuyết về cậu bé lớn vụt lên đánh giặc Ân."],
    ["Truyện \"Con Rồng cháu Tiên\" kể về Lạc Long Quân và ai?", ["Âu Cơ", "Mị Nương", "Tấm", "Chị Hằng"], "Âu Cơ sinh bọc trăm trứng, nở ra trăm người con."],
    ["Theo truyền thuyết, ai làm ra bánh chưng, bánh giầy?", ["Lang Liêu", "Sơn Tinh", "Thạch Sanh", "Chử Đồng Tử"], "Lang Liêu dâng bánh chưng tượng trưng cho đất, bánh giầy cho trời."],
    ["Ai là tác giả Truyện Kiều?", ["Nguyễn Du", "Nguyễn Trãi", "Hồ Xuân Hương", "Tố Hữu"], "Truyện Kiều là kiệt tác thơ lục bát của Nguyễn Du."],
    ["Áo dài là gì của người Việt?", ["Áo truyền thống", "Đồ ngủ", "Đồ bơi", "Áo mưa"], "Áo dài thường mặc trong ngày lễ, Tết, cưới hỏi."],
    ["Múa rối nước biểu diễn ở đâu?", ["Trên mặt nước", "Trên cây", "Trong hang", "Trên mái nhà"], "Con rối đứng trên mặt ao, người điều khiển nấp sau tấm mành."],
    ["Dân ca Quan họ nổi tiếng ở vùng nào?", ["Bắc Ninh", "Cà Mau", "Đà Lạt", "Nha Trang"], "Quan họ Bắc Ninh là di sản văn hoá của nhân loại."],
    ["Chữ viết tiếng Việt ngày nay gọi là?", ["Chữ Quốc ngữ", "Chữ Nôm", "Chữ Hán", "Chữ Phạn"], "Chữ Quốc ngữ dùng bảng chữ cái La-tinh, có thêm dấu thanh."],
    ["Tết Nguyên Đán tính theo lịch nào?", ["Âm lịch", "Dương lịch", "Lịch Tây", "Không theo lịch"], "Mùng 1 tháng Giêng âm lịch là ngày đầu năm mới."],
    ["Tết Trung thu là ngày nào?", ["Rằm tháng 8 âm lịch", "Mùng 1 Tết", "Ngày 1/6", "Rằm tháng Giêng"], "Trung thu trăng tròn và sáng nhất năm."],
    ["Trung thu trẻ em thường rước gì?", ["Đèn ông sao", "Pháo hoa", "Cây thông", "Trứng màu"], "Rước đèn, phá cỗ, ăn bánh nướng bánh dẻo."],
    ["Món bánh truyền thống ngày Tết ở miền Bắc là?", ["Bánh chưng", "Bánh mì", "Bánh pizza", "Bánh kem"], "Miền Nam thường gói bánh tét."],
    ["Đầu năm mới trẻ em thường được nhận gì?", ["Lì xì", "Bài tập", "Hóa đơn", "Vé phạt"], "Phong bao lì xì đỏ chúc trẻ hay ăn chóng lớn."],
    ["Ngày Nhà giáo Việt Nam là ngày nào?", ["20/11", "20/10", "1/6", "8/3"], "Ngày học trò tri ân thầy cô."],
    ["Ngày Quốc tế Thiếu nhi là ngày nào?", ["1/6", "2/9", "20/11", "1/1"], "Ngày Tết của trẻ em trên toàn thế giới."],
    ["Ngày Phụ nữ Việt Nam là ngày nào?", ["20/10", "8/3", "1/6", "14/2"], "8/3 là ngày Quốc tế Phụ nữ, 20/10 là ngày Phụ nữ Việt Nam."],
    ["Giỗ Tổ Hùng Vương là ngày nào?", ["10/3 âm lịch", "2/9", "30/4", "Rằm tháng 7"], "Ngày tưởng nhớ các vua Hùng dựng nước."],
    ["Tết Đoan Ngọ (Tết diệt sâu bọ) là ngày nào?", ["5/5 âm lịch", "1/1 âm lịch", "15/8 âm lịch", "10/3 âm lịch"], "Sáng sớm ăn hoa quả, rượu nếp để \"giết sâu bọ\"."],
    ["Việt Nam nằm ở châu lục nào?", ["Châu Á", "Châu Âu", "Châu Phi", "Châu Mỹ"], "Việt Nam ở khu vực Đông Nam Á."],
    ["Đại dương lớn nhất thế giới là?", ["Thái Bình Dương", "Đại Tây Dương", "Ấn Độ Dương", "Bắc Băng Dương"], "Thái Bình Dương rộng hơn cả toàn bộ đất liền cộng lại."],
    ["Nước nào đông dân nhất thế giới hiện nay?", ["Ấn Độ", "Mỹ", "Nhật Bản", "Brazil"], "Từ năm 2023, Ấn Độ vượt Trung Quốc về dân số."],
    ["Tháp Eiffel ở thành phố nào?", ["Paris", "London", "Tokyo", "Rome"], "Tháp Eiffel là biểu tượng của nước Pháp."],
    ["Kim tự tháp Giza nổi tiếng ở nước nào?", ["Ai Cập", "Mexico", "Ấn Độ", "Hy Lạp"], "Kim tự tháp là lăng mộ của các vua Ai Cập cổ."],
    ["Vạn Lý Trường Thành ở nước nào?", ["Trung Quốc", "Nhật Bản", "Hàn Quốc", "Mông Cổ"], "Bức tường dài hàng nghìn ki-lô-mét xây qua nhiều đời vua."],
    ["Tượng Nữ thần Tự do ở nước nào?", ["Mỹ", "Pháp", "Anh", "Canada"], "Tượng do nước Pháp tặng, đứng ở New York."],
    ["Tiền của Nhật Bản gọi là gì?", ["Yên", "Won", "Đô la", "Bạt"], "Won là tiền Hàn Quốc, Bạt là tiền Thái Lan."],
    ["ASEAN là hiệp hội các nước ở đâu?", ["Đông Nam Á", "Châu Âu", "Châu Phi", "Nam Mỹ"], "Việt Nam là thành viên ASEAN từ năm 1995."],
    ["WHO là tổ chức gì?", ["Y tế thế giới", "Bóng đá thế giới", "Du lịch", "Thời tiết"], "WHO là Tổ chức Y tế Thế giới."],
    ["Thế vận hội mùa hè tổ chức mấy năm một lần?", ["4 năm", "1 năm", "2 năm", "10 năm"], "Thế vận hội (Olympic) mùa hè 4 năm một lần."],
    ["Ngôn ngữ được dùng phổ biến nhất khi giao tiếp quốc tế?", ["Tiếng Anh", "Tiếng La-tinh", "Tiếng Việt", "Tiếng Hy Lạp cổ"], "Tiếng Anh được dùng nhiều trong du lịch, khoa học, buôn bán."],
    ["Hành tinh chúng ta đang sống là?", ["Trái Đất", "Sao Hỏa", "Mặt Trăng", "Sao Kim"], "Trái Đất là hành tinh duy nhất được biết có sự sống."],
    ["Một tuần có mấy ngày?", ["7 ngày", "5 ngày", "10 ngày", "30 ngày"], "Từ thứ Hai đến Chủ nhật là 7 ngày."],
    ["Một năm có mấy tháng?", ["12 tháng", "10 tháng", "7 tháng", "24 tháng"], "Một năm có 12 tháng, khoảng 365 ngày."],
    ["Một giờ có bao nhiêu phút?", ["60 phút", "100 phút", "30 phút", "24 phút"], "Một giờ 60 phút, một phút 60 giây."],
    ["Ở miền Bắc, mùa nào lạnh nhất?", ["Mùa đông", "Mùa hè", "Mùa thu", "Mùa xuân"], "Miền Bắc có bốn mùa, miền Nam chỉ có mùa mưa và mùa khô."],
    ["Con vật nào thường được nuôi để trông nhà?", ["Con chó", "Con gà", "Con cá", "Con thỏ"], "Chó nghe thấy người lạ là sủa báo cho chủ."],
    ["Sữa tươi ta uống hằng ngày phần lớn lấy từ con gì?", ["Con bò", "Con gà", "Con lợn", "Con vịt"], "Bò sữa cho rất nhiều sữa mỗi ngày."],
    ["Muốn gửi thư cho người ở xa thì ra đâu?", ["Bưu điện", "Bệnh viện", "Chợ cá", "Trạm xăng"], "Bưu điện nhận thư, gói hàng và chuyển đi khắp nơi."]
  ];
  SUBJECTS[SUBJ][0] = 'Xã hội';
  if (typeof IMG === 'object' && IMG && IMG['th_the_xa-hoi']) SUBJECTS[SUBJ][1] = 'the_xa-hoi';
  const shuffle = arr => [...arr].sort(() => Math.random() - 0.5);

  const makeQ0 = makeQ;
  globalThis.makeQ = function (subj, used) {
    if (subj !== SUBJ) return makeQ0.apply(this, arguments);
    if (S.sch) S.sch.next = false;
    let free = BANK.map((r, k) => k).filter(k => !used.includes(k));
    if (!free.length) free = BANK.map((r, k) => k);
    const k = free[Math.floor(Math.random() * free.length)], [q, opts, why] = BANK[k];
    used.push(k);
    const choices = shuffle(opts);
    return { q, long: true, choices, ok: choices.indexOf(opts[0]), why };
  };

  // A after an answer: on to the next question (not in the first 0.4 s, so a double press does not skip the why)
  const input0 = schoolInput;
  globalThis.schoolInput = function (btn, now) {
    const c = S.sch;
    if (c && c.subj === SUBJ && c.st === 'ans' && c.cur && c.cur.why) {
      if ((btn === 'A' || btn === 'B') && now - c.t > 400) { c.next = true; c.t = now - WAIT - 1; }
      if (btn === 'B') c.leave = true;
      return;
    }
    return input0.apply(this, arguments);
  };

  const draw0 = drawSchool;
  globalThis.drawSchool = function (now) {
    const c = S.sch;
    if (!c || c.subj !== SUBJ || !c.cur) return draw0.apply(this, arguments);
    const hold = c.st === 'ans' && c.cur.why && !c.next;
    if (hold) c.t = Math.max(c.t, now - WAIT + 50);              // the demo moves on 1.3 s after c.t: not yet
    // the answers drawn smaller when they are wider than their button
    const names = new Set(c.cur.choices), text0 = text;
    globalThis.text = function (s, x, y, size, ...rest) {
      if (names.has(s)) {
        const bold = rest[2] !== false;
        while (size > MIN_PX) { ctx.font = `${bold ? 'bold ' : ''}${size}px Tahoma, sans-serif`; if (ctx.measureText(s).width <= BTN_W) break; size--; }
      }
      return text0.call(this, s, x, y, size, ...rest);
    };
    try { draw0.apply(this, arguments); } finally { globalThis.text = text0; }
    if (c.leave && c.st !== 'ans') { c.leave = false; if (typeof leaveSchool === 'function') return leaveSchool(); }
    if (!hold) return;
    // cô Rắn's why, on a strip under the answers (left of the teacher)
    const right = c.res[c.res.length - 1], head = right ? 'Đúng rồi! ' : `Đáp án: ${c.cur.choices[c.cur.ok]}. `;
    const lines = wrapLines(head + c.cur.why, 456, '14px Tahoma, sans-serif').slice(0, 2);
    ctx.fillStyle = 'rgba(251,246,234,0.95)'; ctx.strokeStyle = right ? '#6aa86a' : '#e8a070'; ctx.lineWidth = 2;
    ctx.beginPath(); ctx.roundRect(28, 348, 480, lines.length > 1 ? 52 : 34, 8); ctx.fill(); ctx.stroke();
    lines.forEach((l, k) => text(l, 40, 365 + k * 18, 14, '#3a2a1a', 'left', false));
    ctx.fillStyle = "#140b07"; ctx.fillRect(0, 456, 640, 24);
    text('A: câu tiếp · B: về', 320, 468, 12, '#f0e4ce', 'center', false, 2);
  };
  globalThis.__xaHoi = { BANK };                                // for the test harness
})();
