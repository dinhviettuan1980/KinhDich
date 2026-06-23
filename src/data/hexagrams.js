// 64 quẻ Kinh Dịch — dữ liệu tĩnh
// Mỗi quẻ: id, tên, thượng quái, hạ quái, ý nghĩa giáo dục (không bói toán)

export const TRIGRAM_VI = {
  qian: 'Càn (☰) — Trời',
  kun:  'Khôn (☷) — Đất',
  zhen: 'Chấn (☳) — Sấm',
  xun:  'Tốn (☴) — Gió',
  kan:  'Khảm (☵) — Nước',
  li:   'Ly (☲) — Lửa',
  gen:  'Cấn (☶) — Núi',
  dui:  'Đoài (☱) — Hồ',
}

export const TRIGRAM_SHORT = {
  qian: 'Càn', kun: 'Khôn', zhen: 'Chấn',
  xun: 'Tốn', kan: 'Khảm', li: 'Ly', gen: 'Cấn', dui: 'Đoài',
}

export const TRIGRAM_ELEMENT = {
  qian: 'Thiên', kun: 'Địa', zhen: 'Lôi',
  xun: 'Phong', kan: 'Thủy', li: 'Hỏa', gen: 'Sơn', dui: 'Trạch',
}

// Nhận diện quái từ 3 hào (bottom→top), value 6/8=âm, 7/9=dương
export function identifyTrigram(threeLines) {
  const bits = threeLines.map(v => (v === 7 || v === 9) ? 1 : 0)
  const key = bits[0] + bits[1] * 2 + bits[2] * 4
  return ['kun','zhen','kan','dui','gen','li','xun','qian'][key]
}

// Bảng tra 64 quẻ theo [thượng quái][hạ quái]
const HEX_TABLE = {
  'qian-qian':1,  'qian-kun':12,  'qian-zhen':25, 'qian-xun':44,
  'qian-kan':6,   'qian-li':13,   'qian-gen':33,  'qian-dui':10,
  'kun-qian':11,  'kun-kun':2,    'kun-zhen':24,  'kun-xun':46,
  'kun-kan':7,    'kun-li':36,    'kun-gen':15,   'kun-dui':19,
  'zhen-qian':34, 'zhen-kun':16,  'zhen-zhen':51, 'zhen-xun':32,
  'zhen-kan':40,  'zhen-li':55,   'zhen-gen':62,  'zhen-dui':54,
  'xun-qian':9,   'xun-kun':20,   'xun-zhen':42,  'xun-xun':57,
  'xun-kan':59,   'xun-li':37,    'xun-gen':53,   'xun-dui':61,
  'kan-qian':5,   'kan-kun':8,    'kan-zhen':3,   'kan-xun':48,
  'kan-kan':29,   'kan-li':63,    'kan-gen':39,   'kan-dui':60,
  'li-qian':14,   'li-kun':35,    'li-zhen':21,   'li-xun':50,
  'li-kan':64,    'li-li':30,     'li-gen':56,    'li-dui':38,
  'gen-qian':26,  'gen-kun':23,   'gen-zhen':27,  'gen-xun':18,
  'gen-kan':4,    'gen-li':22,    'gen-gen':52,   'gen-dui':41,
  'dui-qian':43,  'dui-kun':45,   'dui-zhen':17,  'dui-xun':28,
  'dui-kan':47,   'dui-li':49,    'dui-gen':31,   'dui-dui':58,
}

export function lookupHexagram(upperTrigram, lowerTrigram) {
  return HEX_TABLE[`${upperTrigram}-${lowerTrigram}`] || 1
}

// Tính quẻ biến: hào 9→8, hào 6→7 (âm/dương đổi chỗ)
export function getChangedLines(lines) {
  return lines.map(v => v === 9 ? 8 : v === 6 ? 7 : v)
}

// Hào động là hào có giá trị 6 hoặc 9
export function getMovingLines(lines) {
  return lines.map((v, i) => (v === 6 || v === 9) ? i + 1 : null).filter(Boolean)
}

// 64 quẻ đầy đủ
export const HEXAGRAMS = [
  {
    id: 1, name: 'Thuần Càn', upper: 'qian', lower: 'qian',
    shortMeaning: 'Sức mạnh thuần túy. Thời điểm khởi đầu mạnh mẽ, hành động quyết đoán.',
    lifeMeaning: 'Đây là thời điểm của sức sống và hành động. Bạn đang ở đỉnh của chu kỳ — hãy chủ động dẫn dắt thay vì chờ đợi.',
    businessMeaning: 'Lãnh đạo cần thể hiện rõ tầm nhìn. Đây là lúc khởi động dự án mới, không phải lúc do dự.',
    techMeaning: 'Như kiến trúc thuần microservice — từng thành phần độc lập, mạnh mẽ. Sprint mới cần leadership rõ ràng, không cần ủy ban.',
  },
  {
    id: 2, name: 'Thuần Khôn', upper: 'kun', lower: 'kun',
    shortMeaning: 'Sức mạnh của sự tiếp nhận. Thành công qua hỗ trợ và kiên nhẫn.',
    lifeMeaning: 'Không phải lúc dẫn đầu — hãy hỗ trợ, lắng nghe và cho phép sự việc tự định hình. Đất nuôi dưỡng mọi thứ mà không tranh công.',
    businessMeaning: 'Giai đoạn xây nền móng, đào tạo đội nhóm, củng cố quy trình hơn là tăng trưởng nóng.',
    techMeaning: 'Như infrastructure layer — không ai thấy nhưng mọi thứ đều phụ thuộc. Tập trung vào CI/CD, testing framework, documentation.',
  },
  {
    id: 3, name: 'Thủy Lôi Truân', upper: 'kan', lower: 'zhen',
    shortMeaning: 'Khó khăn ban đầu. Mọi sự khởi đầu đều có thử thách — đây là bình thường.',
    lifeMeaning: 'Giai đoạn hỗn loạn đầu tiên của bất kỳ hành trình mới nào. Kiên trì và tìm sự hỗ trợ thay vì một mình xông pha.',
    businessMeaning: 'Startup giai đoạn đầu, sản phẩm mới ra mắt gặp trục trặc. Cần đồng minh và kiên nhẫn.',
    techMeaning: 'Day 1 của dự án mới: môi trường chưa setup, yêu cầu mờ nhạt, team chưa ăn ý. Đây là bình thường — đừng panic.',
  },
  {
    id: 4, name: 'Sơn Thủy Mông', upper: 'gen', lower: 'kan',
    shortMeaning: 'Học hỏi qua mờ mịt. Người mới bắt đầu cần thầy, cần hướng dẫn.',
    lifeMeaning: 'Sự mờ mịt không phải trở ngại — đó là điều kiện để học. Hãy tìm người hướng dẫn và đặt câu hỏi.',
    businessMeaning: 'Thị trường mới, domain mới — cần nghiên cứu kỹ trước khi hành động. Tuyển mentor hoặc advisor.',
    techMeaning: 'Onboarding developer mới vào codebase phức tạp. Cần documentation tốt, pair programming, patience.',
  },
  {
    id: 5, name: 'Thủy Thiên Nhu', upper: 'kan', lower: 'qian',
    shortMeaning: 'Chờ đợi đúng thời điểm. Kiên nhẫn không phải thụ động mà là chiến lược.',
    lifeMeaning: 'Bạn đã sẵn sàng nhưng thời cơ chưa chín muồi. Hãy nuôi dưỡng bản thân trong thời gian chờ.',
    businessMeaning: 'Product-market fit chưa rõ, hoặc market chưa sẵn sàng. Tiếp tục build nhưng đừng push marketing quá sớm.',
    techMeaning: 'Feature done nhưng chưa release vì dependencies chưa sẵn sàng. Viết test, refactor code trong lúc chờ.',
  },
  {
    id: 6, name: 'Thiên Thủy Tụng', upper: 'qian', lower: 'kan',
    shortMeaning: 'Xung đột và tranh luận. Không nên leo thang — tìm giải pháp thỏa hiệp.',
    lifeMeaning: 'Có sự mâu thuẫn giữa hai lực lượng hay quan điểm. Leo thang sẽ không ai thắng hoàn toàn.',
    businessMeaning: 'Conflict trong team hay với đối tác. Cần người trung gian, tập trung vào lợi ích chung thay vì lập trường.',
    techMeaning: 'Architecture debate kéo dài giữa các senior dev. Cần facilitated decision-making, ADR (Architecture Decision Record).',
  },
  {
    id: 7, name: 'Địa Thủy Sư', upper: 'kun', lower: 'kan',
    shortMeaning: 'Tổ chức và kỷ luật. Thành công đến từ đội ngũ được dẫn dắt tốt.',
    lifeMeaning: 'Cần người lãnh đạo có kỷ luật và chiến lược rõ ràng. Sức mạnh tập thể vượt qua cá nhân xuất sắc.',
    businessMeaning: 'Giai đoạn cần quy trình hóa, standardize, scale team. Đầu tư vào management layer.',
    techMeaning: 'Engineering manager cần thiết lập coding standards, sprint ritual, incident response playbook.',
  },
  {
    id: 8, name: 'Thủy Địa Tỉ', upper: 'kan', lower: 'kun',
    shortMeaning: 'Liên kết và hợp tác. Sức mạnh đến từ sự kết nối đúng người.',
    lifeMeaning: 'Hãy chủ động xây dựng quan hệ. Ai bạn kết nối sẽ định hình con đường của bạn.',
    businessMeaning: 'Partnership, networking, building ecosystem xung quanh sản phẩm. Đừng đi một mình.',
    techMeaning: 'Integrate APIs, build platform integrations, open source community. Kết nối tốt hơn build lại từ đầu.',
  },
  {
    id: 9, name: 'Phong Thiên Tiểu Súc', upper: 'xun', lower: 'qian',
    shortMeaning: 'Tích lũy từng chút nhỏ. Chưa phải lúc bước lớn — hãy chuẩn bị.',
    lifeMeaning: 'Tích lũy kiến thức, sức lực, nguồn lực. Những tiến bộ nhỏ mỗi ngày là nền tảng cho bước nhảy lớn.',
    businessMeaning: 'Giai đoạn MVP, pilot, thử nghiệm nhỏ. Validate trước, scale sau.',
    techMeaning: 'Feature flag, A/B test, canary deployment — rollout từng bước nhỏ thay vì big bang release.',
  },
  {
    id: 10, name: 'Thiên Trạch Lý', upper: 'qian', lower: 'dui',
    shortMeaning: 'Bước đi cẩn thận. Biết mình đang đứng ở đâu và hành xử đúng vai trò.',
    lifeMeaning: 'Hành vi và phong cách giao tiếp quan trọng hơn năng lực thuần túy trong giai đoạn này.',
    businessMeaning: 'Stakeholder management, executive communication, professionalism trong đàm phán.',
    techMeaning: 'Code review etiquette, how you give feedback matters. Technical correctness ≠ right way to communicate.',
  },
  {
    id: 11, name: 'Địa Thiên Thái', upper: 'kun', lower: 'qian',
    shortMeaning: 'Hòa hợp và thịnh vượng. Trời đất giao hòa — mọi thứ đang thuận lợi.',
    lifeMeaning: 'Thời điểm tốt để hành động, mở rộng, kết nối. Năng lượng đang ủng hộ bạn.',
    businessMeaning: 'Bull market, product-market fit found, team chemistry tốt. Đây là lúc accelerate.',
    techMeaning: 'System đang ổn định, team productive, technical debt thấp. Thời điểm ship features nhanh.',
  },
  {
    id: 12, name: 'Thiên Địa Bĩ', upper: 'qian', lower: 'kun',
    shortMeaning: 'Bế tắc và ngưng trệ. Trời đất không thông — giao tiếp tắc nghẽn.',
    lifeMeaning: 'Mọi thứ đang không lưu thông. Đừng ép buộc — rút lui để bảo toàn sức lực và chờ đợi.',
    businessMeaning: 'Sales pipeline frozen, team misalignment, strategy không được execute. Cần reset.',
    techMeaning: 'Tech debt quá nặng, không ship được gì. Cần sprint dọn dẹp, không thêm feature mới.',
  },
  {
    id: 13, name: 'Thiên Hỏa Đồng Nhân', upper: 'qian', lower: 'li',
    shortMeaning: 'Đoàn kết vì mục tiêu chung. Sức mạnh tập thể khi cùng hướng về một tầm nhìn.',
    lifeMeaning: 'Tìm những người cùng chí hướng và xây dựng cộng đồng. Một mình giỏi không bằng cùng nhau.',
    businessMeaning: 'Culture building, mission-driven team, founding team alignment.',
    techMeaning: 'Open source project, inner source, cross-functional squad hướng tới shared OKR.',
  },
  {
    id: 14, name: 'Hỏa Thiên Đại Hữu', upper: 'li', lower: 'qian',
    shortMeaning: 'Sở hữu lớn lao. Thành công và phong phú — nhưng cần quản lý khéo léo.',
    lifeMeaning: 'Bạn đang có nhiều tài nguyên, cơ hội hoặc ảnh hưởng. Trách nhiệm tương xứng với quyền năng.',
    businessMeaning: 'Scale-up phase, funding round, market leader position. Govern wisely.',
    techMeaning: 'Platform với nhiều users, technical influence lớn. Cần governance, deprecation policy, breaking change management.',
  },
  {
    id: 15, name: 'Địa Sơn Khiêm', upper: 'kun', lower: 'gen',
    shortMeaning: 'Khiêm tốn bền vững. Núi nằm dưới đất — tài năng ẩn bên trong.',
    lifeMeaning: 'Thành công thực sự không cần phô trương. Sự khiêm tốn thu hút tôn trọng lâu dài.',
    businessMeaning: 'Underpromise, overdeliver. Không hype quá mức — let the results speak.',
    techMeaning: 'Senior engineer không cần chứng tỏ — viết clean code, mentor junior, fix bugs quietly.',
  },
  {
    id: 16, name: 'Lôi Địa Dự', upper: 'zhen', lower: 'kun',
    shortMeaning: 'Nhiệt tình và sẵn sàng. Năng lượng cao — hành động có động lực.',
    lifeMeaning: 'Khai thác năng lượng tích cực hiện tại. Truyền cảm hứng cho người xung quanh.',
    businessMeaning: 'Launch event, product announcement, team rally. Tận dụng momentum.',
    techMeaning: 'Hackathon, innovation sprint, team outing sau successful release — recharge và inspire.',
  },
  {
    id: 17, name: 'Trạch Lôi Tùy', upper: 'dui', lower: 'zhen',
    shortMeaning: 'Thích nghi và theo dòng. Linh hoạt theo hoàn cảnh là sức mạnh.',
    lifeMeaning: 'Đừng cưỡng lại sự thay đổi — hãy đi cùng dòng chảy trong khi giữ vững nguyên tắc cốt lõi.',
    businessMeaning: 'Pivot khi cần thiết, customer feedback loop, agile response to market.',
    techMeaning: 'Responsive design thinking: adapt UI/UX theo user behavior. Follow data, not assumptions.',
  },
  {
    id: 18, name: 'Sơn Phong Cổ', upper: 'gen', lower: 'xun',
    shortMeaning: 'Sửa chữa và đổi mới. Nhận diện và khắc phục những gì đã hỏng.',
    lifeMeaning: 'Đây là lúc đối mặt với những vấn đề đã bị bỏ qua quá lâu. Dũng cảm để thay đổi.',
    businessMeaning: 'Legacy business model cần transform. Cultural debt, process debt cần addressing.',
    techMeaning: 'Legacy codebase refactoring, security audit, tech debt sprint. "Boy Scout Rule": leave it better than you found it.',
  },
  {
    id: 19, name: 'Địa Trạch Lâm', upper: 'kun', lower: 'dui',
    shortMeaning: 'Tiếp cận và ảnh hưởng. Thời điểm mở rộng tầm với và kết nối.',
    lifeMeaning: 'Cơ hội đang đến gần. Hãy chủ động tiếp cận — không chờ người khác tìm mình.',
    businessMeaning: 'Sales outreach, partnership development, community engagement.',
    techMeaning: 'API adoption campaign, developer relations, tech evangelism — reach out to users chứ không ngồi chờ.',
  },
  {
    id: 20, name: 'Phong Địa Quan', upper: 'xun', lower: 'kun',
    shortMeaning: 'Quan sát và chiêm nghiệm. Trước khi hành động, hãy nhìn thật rõ.',
    lifeMeaning: 'Dừng lại và quan sát toàn cảnh trước khi quyết định. Bức tranh lớn quan trọng hơn chi tiết.',
    businessMeaning: 'Market research, competitive analysis, strategy review trước khi action.',
    techMeaning: 'Observability — metrics, logs, traces trước khi optimize. "Measure twice, cut once."',
  },
  {
    id: 21, name: 'Hỏa Lôi Phệ Hạp', upper: 'li', lower: 'zhen',
    shortMeaning: 'Quyết định và hành động dứt khoát. Cắt bỏ chướng ngại vật.',
    lifeMeaning: 'Vấn đề đang cản trở cần được xử lý trực tiếp, không vòng vo. Quyết đoán là cần thiết.',
    businessMeaning: 'Tough decision: terminate underperformer, cut losing product, enforce policy.',
    techMeaning: 'Deprecate old API, remove dead code, break backward compatibility khi cần — với migration guide rõ ràng.',
  },
  {
    id: 22, name: 'Sơn Hỏa Bí', upper: 'gen', lower: 'li',
    shortMeaning: 'Vẻ đẹp và hình thức. Nhưng bề ngoài không thay thế được bản chất.',
    lifeMeaning: 'Đầu tư vào presentation và communication — nhưng đừng để vẻ ngoài che khuất nội dung thực.',
    businessMeaning: 'Branding, UX polish, pitch deck — quan trọng nhưng không bù được product thiếu value.',
    techMeaning: 'UI polish và design system quan trọng, nhưng không thay thế được performance và reliability.',
  },
  {
    id: 23, name: 'Sơn Địa Bác', upper: 'gen', lower: 'kun',
    shortMeaning: 'Suy giảm và phai tàn. Đây là lúc dừng lại, không phải tiến tới.',
    lifeMeaning: 'Năng lượng đang giảm dần. Bảo toàn sức lực, không cưỡng ép. Chờ chu kỳ mới.',
    businessMeaning: 'Product end-of-life, market shrinking, team burnout. Đừng throw good money after bad.',
    techMeaning: 'System đang xuống cấp. Sunset plan cần thiết hơn là patch thêm vào legacy.',
  },
  {
    id: 24, name: 'Địa Lôi Phục', upper: 'kun', lower: 'zhen',
    shortMeaning: 'Trở lại và phục hồi. Sau tối tăm là bình minh — chu kỳ mới bắt đầu.',
    lifeMeaning: 'Tia sáng đầu tiên sau giai đoạn khó khăn. Đừng vội vã — để mầm non lớn dần.',
    businessMeaning: 'Post-crisis recovery, product relaunch, team rebuild sau restructuring.',
    techMeaning: 'Sau major incident hay migration lớn — gradual ramp-up, monitoring chặt, không rush to full traffic.',
  },
  {
    id: 25, name: 'Thiên Lôi Vô Vọng', upper: 'qian', lower: 'zhen',
    shortMeaning: 'Chân thực và tự nhiên. Hành động xuất phát từ bản chất, không toan tính.',
    lifeMeaning: 'Sự chân thật không cần kế hoạch — cứ là chính mình và làm điều đúng đắn.',
    businessMeaning: 'Authentic marketing, transparent communication với khách hàng và nhà đầu tư.',
    techMeaning: 'Write code because it solves the problem, not to show off. Simple > clever.',
  },
  {
    id: 26, name: 'Sơn Thiên Đại Súc', upper: 'gen', lower: 'qian',
    shortMeaning: 'Tích lũy năng lượng lớn. Kiềm chế sức mạnh — chờ thời điểm thích hợp.',
    lifeMeaning: 'Bạn đang tích lũy kiến thức, kinh nghiệm, nguồn lực. Đừng phóng thích sớm quá.',
    businessMeaning: 'Stealth mode, R&D phase, war chest building. Chuẩn bị kỹ trước khi market.',
    techMeaning: 'Internal tool đang prove out, không rush to open source. Build solid foundation trước khi scale.',
  },
  {
    id: 27, name: 'Sơn Lôi Di', upper: 'gen', lower: 'zhen',
    shortMeaning: 'Nuôi dưỡng đúng cách. Chú ý đến điều gì bạn tiêu thụ và cung cấp.',
    lifeMeaning: 'Cẩn thận với những gì bạn "ăn" — kiến thức, thông tin, mối quan hệ đều nuôi dưỡng hay làm hỏng bạn.',
    businessMeaning: 'Talent development, knowledge management, team nutrition — không chỉ OKR mà còn culture.',
    techMeaning: 'Tech stack choices là "diet" của team. Không phải cứ trend là tốt — chọn đúng tool cho context.',
  },
  {
    id: 28, name: 'Trạch Phong Đại Quá', upper: 'dui', lower: 'xun',
    shortMeaning: 'Quá tải và áp lực cực đại. Cần hành động táo bạo để thoát khỏi bế tắc.',
    lifeMeaning: 'Tình huống này không thể tiếp tục — cần thay đổi căn bản, không phải điều chỉnh nhỏ.',
    businessMeaning: 'Burn rate quá cao, market window đang đóng, cần pivot quyết liệt hoặc shut down.',
    techMeaning: 'System đang không thể scale theo cách hiện tại — cần re-architecture, không phải optimize.',
  },
  {
    id: 29, name: 'Thuần Khảm', upper: 'kan', lower: 'kan',
    shortMeaning: 'Nguy hiểm liên tiếp. Giữ vững tâm trí và đi qua từng thử thách một.',
    lifeMeaning: 'Khó khăn chồng chất — nhưng nước chảy đá mòn. Kiên trì đi qua, không bỏ cuộc.',
    businessMeaning: 'Consecutive quarters down, back-to-back crises. Preserve cash, trust process.',
    techMeaning: 'Incident sau incident. Cần bình tĩnh: triage → isolate → fix → post-mortem, không panic.',
  },
  {
    id: 30, name: 'Thuần Ly', upper: 'li', lower: 'li',
    shortMeaning: 'Ánh sáng và sự rõ ràng. Phụ thuộc vào điều gì đó để sáng lên.',
    lifeMeaning: 'Bạn tỏa sáng khi được gắn với đúng người, đúng mục đích. Tìm điều làm bạn bừng sáng.',
    businessMeaning: 'Clarity of purpose, brand clarity, vision statement rõ ràng hơn roadmap.',
    techMeaning: 'Observability, dashboards rõ ràng. Hệ thống cần "ánh sáng" — metrics và logs tốt.',
  },
  {
    id: 31, name: 'Trạch Sơn Hàm', upper: 'dui', lower: 'gen',
    shortMeaning: 'Thu hút và cảm ứng. Sức mạnh của kết nối cảm xúc.',
    lifeMeaning: 'Ảnh hưởng tự nhiên — không cưỡng ép mà thu hút. Người lãnh đạo tốt nhất là người được follow tự nguyện.',
    businessMeaning: 'Inbound marketing, product-led growth, community-driven acquisition.',
    techMeaning: 'Developer experience (DX) — API design tốt, documentation hấp dẫn thu hút developers tự nhiên.',
  },
  {
    id: 32, name: 'Lôi Phong Hằng', upper: 'zhen', lower: 'xun',
    shortMeaning: 'Bền vững và nhất quán. Sức mạnh đến từ sự kiên định theo thời gian.',
    lifeMeaning: 'Thói quen tốt duy trì lâu dài tạo ra kết quả phi thường. Consistency beats intensity.',
    businessMeaning: 'Sustainable business model, consistent brand voice, repeatable sales process.',
    techMeaning: 'Reliable systems win. 99.9% uptime built through discipline, not heroics. On-call rotation đều đặn.',
  },
  {
    id: 33, name: 'Thiên Sơn Độn', upper: 'qian', lower: 'gen',
    shortMeaning: 'Rút lui có chiến lược. Đôi khi lùi lại là cách tốt nhất để tiến về sau.',
    lifeMeaning: 'Biết khi nào cần rút để bảo toàn lực lượng. Rút lui khéo léo không phải thất bại.',
    businessMeaning: 'Exit non-core market, step back from partnership không hiệu quả, resign gracefully.',
    techMeaning: 'Deprecate feature không ai dùng, remove dead code, sunset old service — graceful shutdown.',
  },
  {
    id: 34, name: 'Lôi Thiên Đại Tráng', upper: 'zhen', lower: 'qian',
    shortMeaning: 'Sức mạnh vĩ đại. Thời điểm đỉnh cao — nhưng sức mạnh cần được kiểm soát.',
    lifeMeaning: 'Bạn đang rất mạnh — nhưng đừng để sức mạnh trở thành kiêu ngạo. Dùng nó có trách nhiệm.',
    businessMeaning: 'Market leader, moat mạnh — nhưng cẩn thận với complacency và anti-competitive behavior.',
    techMeaning: 'High traffic, dominant platform — nhưng power cần responsibility: backward compat, security, accessibility.',
  },
  {
    id: 35, name: 'Hỏa Địa Tấn', upper: 'li', lower: 'kun',
    shortMeaning: 'Tiến bộ rõ ràng. Tiến nhanh và được công nhận.',
    lifeMeaning: 'Công sức đang được ghi nhận. Đây là thời điểm để nổi bật và tiến lên phía trước.',
    businessMeaning: 'Growth phase, increasing market share, getting recognized by industry.',
    techMeaning: 'Feature velocity cao, user growth tốt, được reference ở conference. Ride the wave.',
  },
  {
    id: 36, name: 'Địa Hỏa Minh Di', upper: 'kun', lower: 'li',
    shortMeaning: 'Ánh sáng bị che khuất. Ẩn mình và chờ đợi thời cơ.',
    lifeMeaning: 'Môi trường không thuận lợi — giữ tài năng và trí tuệ bên trong, đừng phô bày.',
    businessMeaning: 'Hostile market, hostile management — survive, không phải thrive. Bảo toàn resources.',
    techMeaning: 'Legacy environment không cho phép thay đổi. Document everything, build skills quietly, look for exit.',
  },
  {
    id: 37, name: 'Phong Hỏa Gia Nhân', upper: 'xun', lower: 'li',
    shortMeaning: 'Gia đình và đội nhóm. Trật tự và vai trò rõ ràng tạo nên sức mạnh.',
    lifeMeaning: 'Mỗi người trong team có vai trò, trách nhiệm rõ ràng. Khi đúng người đúng việc, mọi thứ vận hành trơn tru.',
    businessMeaning: 'Org design, RACI matrix, clear ownership. Team culture as extended family.',
    techMeaning: 'Clear code ownership, on-call rotation fair, knowledge sharing — no single point of failure.',
  },
  {
    id: 38, name: 'Hỏa Trạch Khuê', upper: 'li', lower: 'dui',
    shortMeaning: 'Đối lập và bất đồng. Khác biệt không phải xung đột — tìm điểm chung.',
    lifeMeaning: 'Hai quan điểm đối lập có thể cùng tồn tại. Tìm điều kết nối thay vì khuếch đại sự khác biệt.',
    businessMeaning: 'Cross-functional tension, B2B negotiation, co-founder disagreement — seek alignment.',
    techMeaning: 'Frontend vs backend priorities, engineering vs product — conflict productive khi được facilitated tốt.',
  },
  {
    id: 39, name: 'Thủy Sơn Kiển', upper: 'kan', lower: 'gen',
    shortMeaning: 'Trở ngại và khó khăn. Hãy dừng lại và tìm sự hỗ trợ.',
    lifeMeaning: 'Không phải lúc xông thẳng vào khó khăn. Đánh giá lại, tìm đồng minh, chọn đường vòng nếu cần.',
    businessMeaning: 'Regulatory hurdle, competitor blockade, technical blocker. Không cần brute force.',
    techMeaning: 'Blocker trong sprint: không nên spin wheels — escalate, find workaround, unblock bằng cách khác.',
  },
  {
    id: 40, name: 'Lôi Thủy Giải', upper: 'zhen', lower: 'kan',
    shortMeaning: 'Giải phóng và tháo gỡ. Căng thẳng được giải tỏa, con đường mở ra.',
    lifeMeaning: 'Nút thắt đang được tháo gỡ. Đây là lúc tha thứ, buông bỏ và tiến về phía trước.',
    businessMeaning: 'Debt restructure, pivot thành công, key hire giải quyết bottleneck.',
    techMeaning: 'Tech debt được trả, bug cluster được fix, performance bottleneck identified và resolved.',
  },
  {
    id: 41, name: 'Sơn Trạch Tổn', upper: 'gen', lower: 'dui',
    shortMeaning: 'Giảm bớt để lợi lớn hơn. Hy sinh ngắn hạn cho lợi ích dài hạn.',
    lifeMeaning: 'Đôi khi bớt đi mới đủ sức để tiến xa. Tinh gọn tạo ra sức mạnh.',
    businessMeaning: 'Cost cutting, headcount reduction, feature pruning — painful but necessary.',
    techMeaning: 'Remove features nobody uses, simplify API surface, reduce dependencies — less is more.',
  },
  {
    id: 42, name: 'Phong Lôi Ích', upper: 'xun', lower: 'zhen',
    shortMeaning: 'Gia tăng và phong phú. Thời điểm tốt để đầu tư và mở rộng.',
    lifeMeaning: 'Gió đang đẩy. Đây là thời điểm hành động, đầu tư vào bản thân và người khác.',
    businessMeaning: 'Growth investment, team expansion, product line extension — favorable conditions.',
    techMeaning: 'Invest in platform capabilities, developer tools, monitoring — pays dividends later.',
  },
  {
    id: 43, name: 'Trạch Thiên Quải', upper: 'dui', lower: 'qian',
    shortMeaning: 'Quyết đoán và công khai. Giải quyết vấn đề thẳng thắn, không che giấu.',
    lifeMeaning: 'Đã đến lúc nói thẳng về điều cần thay đổi. Không vòng vo hay ẩn nấp.',
    businessMeaning: 'Public announcement of pivot, transparent layoff communication, whistleblowing nếu cần.',
    techMeaning: 'Public incident report (post-mortem), breaking change announcement rõ ràng, không âm thầm deprecate.',
  },
  {
    id: 44, name: 'Thiên Phong Cấu', upper: 'qian', lower: 'xun',
    shortMeaning: 'Gặp gỡ và cơ hội. Điều mới xuất hiện — quan sát kỹ trước khi đón nhận.',
    lifeMeaning: 'Người mới hay cơ hội mới xuất hiện. Hấp dẫn — nhưng hãy thận trọng, đánh giá kỹ trước khi cam kết.',
    businessMeaning: 'Inbound deal, partnership offer, acquisition interest — due diligence trước.',
    techMeaning: 'New vendor, new framework, new cloud service — evaluate trước khi adopt. Vendor lock-in risk.',
  },
  {
    id: 45, name: 'Trạch Địa Tụy', upper: 'dui', lower: 'kun',
    shortMeaning: 'Tụ họp và hội tụ. Sức mạnh của cộng đồng khi cùng chung mục đích.',
    lifeMeaning: 'Thời điểm để convene, align, celebrate. Đám đông có sức mạnh riêng khi hướng đúng.',
    businessMeaning: 'Company offsite, product launch event, community summit.',
    techMeaning: 'Team retrospective, all-hands, engineering summit — align trên direction và celebrate wins.',
  },
  {
    id: 46, name: 'Địa Phong Thăng', upper: 'kun', lower: 'xun',
    shortMeaning: 'Leo lên từng bước. Tiến bộ chắc chắn và bền vững.',
    lifeMeaning: 'Như cây mọc từ đất — từng từng tiến lên. Đừng vội — nền tảng vững thì thành công bền.',
    businessMeaning: 'Organic growth, career ladder climbing, market penetration từng bước.',
    techMeaning: 'Incremental improvement: weekly release nhỏ tốt hơn monthly big bang. Compound effect.',
  },
  {
    id: 47, name: 'Trạch Thủy Khốn', upper: 'dui', lower: 'kan',
    shortMeaning: 'Kiệt sức và bế tắc. Hãy giữ vững tinh thần trong nghịch cảnh.',
    lifeMeaning: 'Đang ở đáy của chu kỳ. Giữ vững giá trị cốt lõi, đừng từ bỏ trong khi đang ở đáy.',
    businessMeaning: 'Cash crunch, team exhausted, product không tăng trưởng. Triage priorities, không spiral.',
    techMeaning: 'Burnout trong team, technical debt overwhelming, incident fatigue. Cần intervention ngay.',
  },
  {
    id: 48, name: 'Thủy Phong Tỉnh', upper: 'kan', lower: 'xun',
    shortMeaning: 'Nguồn nước không cạn. Nền tảng sâu xa, kiến thức luôn có giá trị.',
    lifeMeaning: 'Một số giá trị cốt lõi không bao giờ thay đổi dù thế giới xung quanh đổi thay.',
    businessMeaning: 'Core competency, IP, brand equity — những thứ tạo ra moat thực sự.',
    techMeaning: 'Domain knowledge, clean architecture, good abstractions — investment trả cổ tức mãi.',
  },
  {
    id: 49, name: 'Trạch Hỏa Cách', upper: 'dui', lower: 'li',
    shortMeaning: 'Cách mạng và thay đổi căn bản. Đây là lúc transform, không chỉ improve.',
    lifeMeaning: 'Sự thay đổi sâu sắc là cần thiết và đúng lúc. Đừng chỉ patch — hãy rebuild.',
    businessMeaning: 'Digital transformation, business model disruption, complete rebranding.',
    techMeaning: 'Rewrite from scratch khi justified (hiếm nhưng có lúc đúng), re-architecture, platform migration.',
  },
  {
    id: 50, name: 'Hỏa Phong Đỉnh', upper: 'li', lower: 'xun',
    shortMeaning: 'Chuyển hóa và nấu nướng. Biến nguyên liệu thô thành giá trị cao.',
    lifeMeaning: 'Quá trình biến đổi đang diễn ra — kiên nhẫn chờ kết quả chín muồi.',
    businessMeaning: 'R&D to product pipeline, incubation program, talent development trở thành leaders.',
    techMeaning: 'Data pipeline: raw data → insights. ML training, compilation, build pipeline — transformation takes time.',
  },
  {
    id: 51, name: 'Thuần Chấn', upper: 'zhen', lower: 'zhen',
    shortMeaning: 'Sốc và kích động. Cú sốc đánh thức — nhưng sau hoảng loạn là rõ ràng.',
    lifeMeaning: 'Cú sốc bất ngờ làm lay chuyển mọi thứ. Người vượt qua tốt là người phục hồi nhanh, không phải người không bị ảnh hưởng.',
    businessMeaning: 'Market shock, sudden competitor, unexpected PR crisis. Resilience over immunity.',
    techMeaning: 'Major production incident, data breach, unexpected traffic spike — chaos engineering mindset.',
  },
  {
    id: 52, name: 'Thuần Cấn', upper: 'gen', lower: 'gen',
    shortMeaning: 'Tĩnh lặng và dừng lại. Biết khi nào cần dừng là trí tuệ.',
    lifeMeaning: 'Không phải lúc nào cũng cần hành động. Đôi khi dừng lại là quyết định khôn ngoan nhất.',
    businessMeaning: 'Feature freeze, decision moratorium, pause before major commitment.',
    techMeaning: 'Stop và think trước khi commit to irreversible decision. "Sleep on it" là good engineering practice.',
  },
  {
    id: 53, name: 'Phong Sơn Tiệm', upper: 'xun', lower: 'gen',
    shortMeaning: 'Tiến dần từng bước. Như chim di cư — có lộ trình, không vội vã.',
    lifeMeaning: 'Những thay đổi tốt nhất diễn ra từ từ và có trật tự. Đừng skip steps.',
    businessMeaning: 'Controlled growth, staged rollout, phased transformation — không rush.',
    techMeaning: 'Canary release, feature flags, progressive rollout — không big bang deployment.',
  },
  {
    id: 54, name: 'Lôi Trạch Quy Muội', upper: 'zhen', lower: 'dui',
    shortMeaning: 'Vị trí chưa phù hợp. Hãy biết mình đang ở đâu trong tổ chức.',
    lifeMeaning: 'Bạn có thể có năng lực nhưng vị trí chưa phù hợp. Hãy kiên nhẫn và hiểu rõ context.',
    businessMeaning: 'Junior in important role without authority, contractor influence bị giới hạn.',
    techMeaning: 'Developer không có access cần thiết, consultant không được nghe. Clarify scope và authority trước.',
  },
  {
    id: 55, name: 'Lôi Hỏa Phong', upper: 'zhen', lower: 'li',
    shortMeaning: 'Đỉnh cao và sung mãn. Nhưng đỉnh cao cũng là lúc bắt đầu xuống.',
    lifeMeaning: 'Đây là đỉnh của chu kỳ hiện tại. Tận hưởng nhưng cũng chuẩn bị cho giai đoạn tiếp theo.',
    businessMeaning: 'Peak quarter, record ARR, team at highest morale — plan for sustainability.',
    techMeaning: 'System at peak performance — không phải lúc add complexity. Maintain và prepare next gen.',
  },
  {
    id: 56, name: 'Hỏa Sơn Lữ', upper: 'li', lower: 'gen',
    shortMeaning: 'Du hành và tạm thời. Không có gốc rễ — hãy linh hoạt và cẩn thận.',
    lifeMeaning: 'Bạn đang trong giai đoạn chuyển tiếp, chưa ổn định. Nhẹ nhàng, linh hoạt, không đầu tư quá lớn.',
    businessMeaning: 'Contractor/consultant mode, market testing, temporary setup — không build permanent infrastructure.',
    techMeaning: 'Prototype, spike, throwaway code — viết để học, không để production. Don\'t over-engineer.',
  },
  {
    id: 57, name: 'Thuần Tốn', upper: 'xun', lower: 'xun',
    shortMeaning: 'Thấm nhuần và thuyết phục từ từ. Gió nhẹ nhưng uốn cong cả cây lớn.',
    lifeMeaning: 'Ảnh hưởng thật sự không cần ồn ào. Kiên trì thuyết phục nhẹ nhàng hiệu quả hơn áp lực.',
    businessMeaning: 'Thought leadership, content marketing, gentle sales cycle thay vì hard sell.',
    techMeaning: 'Gradual adoption của best practices — pair programming, code review culture — không mandate.',
  },
  {
    id: 58, name: 'Thuần Đoài', upper: 'dui', lower: 'dui',
    shortMeaning: 'Vui vẻ và giao tiếp. Niềm vui chân thành lan tỏa và thu hút.',
    lifeMeaning: 'Thời điểm kết nối, chia sẻ và tận hưởng. Niềm vui không phải sao lãng mà là nhiên liệu.',
    businessMeaning: 'Team celebration, customer delight, community joy — culture as competitive advantage.',
    techMeaning: 'Developer joy matters: good tooling, no unnecessary meetings, autonomy — không chỉ salary.',
  },
  {
    id: 59, name: 'Phong Thủy Hoán', upper: 'xun', lower: 'kan',
    shortMeaning: 'Phân tán và hòa tan. Phá vỡ rào cản, kết nối điều đã tách biệt.',
    lifeMeaning: 'Những rào cản cứng nhắc đang được hóa giải. Sự chảy tràn có thể là điều tốt.',
    businessMeaning: 'Breaking silos, cross-team collaboration, market expansion vượt biên giới.',
    techMeaning: 'Monolith → microservices, breaking silos between frontend/backend/data teams.',
  },
  {
    id: 60, name: 'Thủy Trạch Tiết', upper: 'kan', lower: 'dui',
    shortMeaning: 'Tiết chế và giới hạn. Biên giới rõ ràng tạo nên trật tự.',
    lifeMeaning: 'Giới hạn không phải hạn chế — đó là định nghĩa. Biết mình dừng ở đâu là trí tuệ.',
    businessMeaning: 'Scope management, budget discipline, SLA definition — boundaries enable focus.',
    techMeaning: 'Rate limiting, API quotas, resource constraints — boundaries make systems reliable.',
  },
  {
    id: 61, name: 'Phong Trạch Trung Phu', upper: 'xun', lower: 'dui',
    shortMeaning: 'Tin tưởng và sự chân thành. Sự thật nội tâm lan tỏa ra bên ngoài.',
    lifeMeaning: 'Khi bạn thực sự tin vào điều mình làm, người khác cảm nhận được điều đó.',
    businessMeaning: 'Authentic leadership, genuine customer relationships, trust-based sales.',
    techMeaning: 'Code với integrity: không hack workaround để đáp ứng deadline, honest về technical debt.',
  },
  {
    id: 62, name: 'Lôi Sơn Tiểu Quá', upper: 'zhen', lower: 'gen',
    shortMeaning: 'Vượt quá một chút. Hành động nhỏ, thận trọng — không phải bước nhảy lớn.',
    lifeMeaning: 'Đây không phải lúc tham vọng lớn. Làm tốt những việc nhỏ trước mắt.',
    businessMeaning: 'Incremental feature release, small pivots, test trước khi commit lớn.',
    techMeaning: 'Small PRs, small commits, ship frequently. "If it\'s painful, do it more often."',
  },
  {
    id: 63, name: 'Thủy Hỏa Ký Tế', upper: 'kan', lower: 'li',
    shortMeaning: 'Đã hoàn thành nhưng chưa kết thúc. Thành công tạo ra trách nhiệm mới.',
    lifeMeaning: 'Mọi thứ đang ổn định và cân bằng — nhưng đây không phải điểm kết. Duy trì và chuẩn bị tiếp.',
    businessMeaning: 'Product-market fit achieved — bây giờ scale bền vững, không để churn ăn mòn.',
    techMeaning: 'System live và stable — không phải lúc ăn mừng và forget. Monitor, maintain, improve.',
  },
  {
    id: 64, name: 'Hỏa Thủy Vị Tế', upper: 'li', lower: 'kan',
    shortMeaning: 'Chưa hoàn thành. Đang trên đường — thời điểm chuyển tiếp đầy tiềm năng.',
    lifeMeaning: 'Hành trình vẫn đang tiếp diễn. Chưa đến đích — nhưng đã có đủ ánh sáng để tiếp tục.',
    businessMeaning: 'Pre-revenue, beta stage, Series A không đảm bảo thành công — vẫn cần execute.',
    techMeaning: 'MVP shipped nhưng not done — iterating, learning, improving. The journey is the destination.',
  },
]

// Tra cứu theo id
export function getHexagramById(id) {
  return HEXAGRAMS.find(h => h.id === id) || HEXAGRAMS[0]
}

// Tính quẻ từ 6 hào (index 0 = hào 1 = hào dưới cùng)
export function computeHexagrams(lines) {
  const lower = identifyTrigram(lines.slice(0, 3))
  const upper = identifyTrigram(lines.slice(3, 6))
  const origId = lookupHexagram(upper, lower)

  const changedLines = getChangedLines(lines)
  const changedLower = identifyTrigram(changedLines.slice(0, 3))
  const changedUpper = identifyTrigram(changedLines.slice(3, 6))
  const changedId = lookupHexagram(changedUpper, changedLower)

  const movingLines = getMovingLines(lines)

  return {
    original: getHexagramById(origId),
    changed: movingLines.length > 0 ? getHexagramById(changedId) : null,
    movingLines,
    lines,
    changedLines,
    upperTrigram: upper,
    lowerTrigram: lower,
  }
}
