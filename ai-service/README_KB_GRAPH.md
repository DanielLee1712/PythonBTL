# 4. Câu 2b — Knowledge Base Graph (KB_Graph)

## 4.1 Giải Thích Kiến Trúc KB Graph

KB_Graph mô hình hóa hệ thống E-Commerce dưới dạng một **đồ thị tri thức (Knowledge Graph) bipartite**, trong đó hai loại node là `User` và `Product` được liên kết qua các cạnh mang thông tin **hành vi (action type)** và **trọng số (weight)** tương ứng với mức độ tương tác.

- **Node Users (tím):** Đại diện cho **500** khách hàng trong hệ thống.
- **Node Products (xanh lá):** Đại diện cho **50** sản phẩm trong catalog E-Commerce.
- **Edges (cạnh màu sắc theo loại):** `view` (xanh dương), `click` (đỏ), `add_to_cart` (xanh lá), `purchase` (vàng), `search` (cam), `wishlist` (xám), `remove_from_cart` (hồng nhạt), `rate` (hồng đậm).
- **Edge Weight:** Được tính theo công thức tích lũy:

$$weight(u,p,action) = base\_weight(action) \times count(u,p,action)$$

Thang điểm base weight: từ **1.0** (`remove_from_cart`, ít giá trị nhất) đến **4.5** (`purchase`, quan trọng nhất). Weights phục vụ thuật toán gợi ý Collaborative Filtering và Graph-based scoring.

| Hành vi | Base Weight | Mô tả |
|:---|:---:|:---|
| `remove_from_cart` | 1.0 | Ít giá trị nhất — bỏ sản phẩm khỏi giỏ |
| `view` | 1.5 | Xem trang sản phẩm |
| `click` | 2.0 | Nhấp vào sản phẩm |
| `wishlist` | 2.0 | Thêm vào danh sách yêu thích |
| `search` | 2.5 | Tìm kiếm sản phẩm |
| `add_to_cart` | 3.0 | Thêm vào giỏ hàng |
| `rate` | 3.5 | Đánh giá sản phẩm |
| `purchase` | 4.5 | Mua hàng — quan trọng nhất |

### Schema Neo4j (Production)

```
(:User {id})
(:Product {id})
(u)-[:INTERACTS_WITH {action, count, first_ts, last_ts, weight}]->(p)
```

- **Aggregation key:** `(user_id, product_id, action)` — mỗi cặp user-product-action là một relationship duy nhất, tích lũy `count` và `weight` theo thời gian.

### Công nghệ triển khai

| Công nghệ | Vai trò |
|:---|:---|
| **NetworkX** | Xây dựng và xử lý đồ thị ở tầng phân tích/experiment |
| **PyVis** | Trực quan hóa đồ thị dạng dynamic HTML tương tác |
| **Neo4j** | Graph database production để lưu trữ và truy vấn Cypher |

---

## 4.2 Biểu Đồ KB Graph — User-Product Interaction Network

![KB_Graph Network — 30 users × 34 products. Bipartite graph visualize các cluster tương tác.](reports/kb_graph/plots/kb_graph_network.png)

*Hình 5.1: KB_Graph Network — 30 users × 34 products (subgraph) với các edges tương tác nổi bật. Bipartite graph cho phép quan sát các cụm (cluster) tương tác: nhóm users có hành vi tương đồng thường liên kết tới các products tương tự. Độ dày cạnh vàng (`purchase`) phản ánh sức mua cao. Ngoài static PNG, đồ thị còn có phiên bản interactive HTML (`reports/kb_graph/kb_graph.html`) cho phép zoom, kéo thả và hover xem chi tiết từng node/edge.*

---

## 4.3 Thống Kê Topology Đồ Thị

![KB_Graph Statistics — User Out-Degree, Product In-Degree Distribution, và Action Frequency](reports/kb_graph/plots/kb_graph_stats.png)

*Hình 5.2: KB_Graph Statistics — gồm 3 thành phần:*
- ***User Out-Degree (Distinct Products):*** *Phần lớn users tương tác 7–8 sản phẩm (distinct). Phân phối tập trung ở khoảng 6–8, cho thấy users trong hệ thống có mức độ khám phá sản phẩm tương đối đồng đều.*
- ***Product In-Degree (Distinct Users):*** *Phần lớn products nhận tương tác từ 65–90 users (distinct), cho thấy catalog sản phẩm được phân bổ khá đều, không có hiện tượng quá tập trung vào vài sản phẩm.*
- ***Action Frequency:*** `view` *chiếm ưu thế (~950 events), tiếp theo là* `click` *(~750) và* `search` *(~650). Phản ánh phễu hành vi điển hình: xem → nhấp → tìm kiếm → thêm giỏ → mua.*

---

## 4.4 User × Action Heatmap (Top 20 Users)

![User × Action Heatmap — Heatmap hành vi của 20 users hoạt động nhiều nhất](reports/kb_graph/plots/kb_graph_heatmap.png)

*Hình 5.3: Heatmap hành vi của 20 users hoạt động nhiều nhất (xếp theo tổng event). Màu đậm = cao nhất. Quan sát:*
- *`view` và `wishlist` luôn là hành vi thống trị ở hầu hết users (cột sáng nhất).*
- *`search` và `click` ở mức trung bình — phản ánh giai đoạn khám phá sản phẩm.*
- *User 498 nổi bật với tần suất `view` cực cao (vùng nâu đậm), cho thấy hành vi "window shopping" mạnh.*
- *`purchase` phân bố thưa hơn — chỉ một số users thực sự chuyển đổi thành giao dịch mua.*

---

## 4.5 Dữ Liệu Mẫu 20 Cạnh (Edge Matrix)

Mỗi cạnh trong KB_Graph lưu trữ mối quan hệ giữa User và Product kèm trọng số và loại hành vi. Bảng dưới hiển thị **20 cạnh có trọng số cao nhất** (top theo `weight`):

| source_user | target_product | weight | edge_type |
|:---|:---|:---:|:---|
| User 181 | Product 38 | 9.0 | purchase |
| User 320 | Product 41 | 9.0 | purchase |
| User 296 | Product 28 | 9.0 | purchase |
| User 368 | Product 10 | 6.0 | add_to_cart |
| User 288 | Product 28 | 5.0 | search |
| User 289 | Product 15 | 5.0 | search |
| User 78 | Product 47 | 5.0 | search |
| User 102 | Product 9 | 4.5 | purchase |
| User 416 | Product 22 | 4.5 | purchase |
| User 492 | Product 22 | 4.5 | purchase |
| User 299 | Product 11 | 4.5 | purchase |
| User 206 | Product 9 | 4.5 | purchase |
| User 223 | Product 9 | 4.5 | purchase |
| User 254 | Product 9 | 4.5 | purchase |
| User 488 | Product 22 | 4.5 | purchase |
| User 334 | Product 11 | 4.5 | purchase |
| User 256 | Product 22 | 4.5 | purchase |
| User 291 | Product 11 | 4.5 | purchase |
| User 42 | Product 11 | 4.5 | purchase |
| User 291 | Product 9 | 4.5 | purchase |

*Bảng 5.1: 20 cạnh mẫu từ KB_Graph Edge Matrix. Nhận xét: 3 cạnh có trọng số cao nhất (9.0) đều là `purchase` với `count=2` (mua 2 lần). Product 9, Product 11, Product 22 xuất hiện nhiều lần — cho thấy đây là các sản phẩm best-seller của hệ thống.*

---

## 4.6 Cypher Query Mẫu (Neo4j)

### Tạo node và edge trong Neo4j (API realtime)

```cypher
// Tạo hoặc cập nhật node User, Product, và relationship INTERACTS_WITH
MERGE (u:User {id: $user_id})
MERGE (p:Product {id: $product_id})
MERGE (u)-[r:INTERACTS_WITH {action: $action}]->(p)
ON CREATE SET
  r.count = 1,
  r.first_ts = $event_ts,
  r.last_ts = $event_ts,
  r.weight = $action_weight
ON MATCH SET
  r.count = r.count + 1,
  r.last_ts = $event_ts,
  r.weight = r.weight + $action_weight;
```

### Truy vấn sản phẩm tương tự (Collaborative Filtering)

```cypher
// Tìm sản phẩm tương tự dựa trên shared users
MATCH (u:User)-[:INTERACTS_WITH]->(p:Product {id: $product_id})
MATCH (u)-[:INTERACTS_WITH]->(similar:Product)
WHERE similar.id <> $product_id
RETURN similar.id AS product_id, COUNT(DISTINCT u) AS shared_users
ORDER BY shared_users DESC
LIMIT 5;
```

### Truy vấn sản phẩm tương tự (phiên bản có trọng số)

```cypher
// Collaborative Filtering với scoring dựa trên tổng weight
MATCH (u:User)-[r1:INTERACTS_WITH]->(p:Product {id: $product_id})
MATCH (u)-[r2:INTERACTS_WITH]->(similar:Product)
WHERE similar.id <> $product_id
WITH similar, sum(r1.weight + r2.weight) AS score, COUNT(DISTINCT u) AS shared_users
RETURN similar.id AS product_id, shared_users, score
ORDER BY score DESC
LIMIT 5;
```

### Top products theo lượt mua

```cypher
MATCH (:User)-[r:INTERACTS_WITH {action: 'purchase'}]->(p:Product)
RETURN p.id AS product_id, sum(r.count) AS purchase_count, sum(r.weight) AS purchase_weight
ORDER BY purchase_count DESC
LIMIT 10;
```

---

## 4.7 Cách Chạy & Tái Tạo Kết Quả

### Load dữ liệu vào Neo4j

```bash
# Từ thư mục ai-service
python scripts/load_graph_data.py --csv data_user500.csv

# Hoặc reset toàn bộ graph trước khi load
python scripts/load_graph_data.py --csv data_user500.csv --reset
```

### Sinh báo cáo (figures + markdown)

```bash
python scripts/kb_graph_report.py --out reports/kb_graph
```

**Output sinh ra:**
- `reports/kb_graph/KB_Graph_Report.md` — Báo cáo markdown tự động
- `reports/kb_graph/plots/kb_graph_network.png` — Biểu đồ network (static)
- `reports/kb_graph/plots/kb_graph_stats.png` — Thống kê topology
- `reports/kb_graph/plots/kb_graph_heatmap.png` — Heatmap user × action
- `reports/kb_graph/kb_graph.html` — Đồ thị interactive (PyVis)
- `reports/kb_graph/edge_matrix_top20.csv` — 20 cạnh trọng số cao nhất

### Validate dữ liệu đã load

```bash
python scripts/validate_graph_data.py --csv data_user500.csv
```
