# Hướng dẫn các câu lệnh Neo4j phục vụ Demo

File này chứa các câu lệnh (Cypher queries) thông dụng để bạn có thể copy/paste vào Neo4j Browser (thường truy cập qua `http://localhost:7474`) để kiểm tra dữ liệu và so sánh với kết quả từ Chatbot hoặc Search.

## 1. Xem Graph của một Customer cụ thể
Lệnh này rất hữu ích để kiểm tra xem một khách hàng (ví dụ: `customer1`) đã tương tác với những sản phẩm nào, từ đó đối chiếu xem AI Chatbot hoặc phần Search gợi ý có đúng theo lịch sử của user này không.

```cypher
// Xem toàn bộ tương tác của customer1
MATCH (u:User {id: '1'})-[r:INTERACTS_WITH]->(p:Product)
RETURN u, r, p
```

*Mẹo*: Trên giao diện Neo4j Browser, sau khi chạy lệnh này, bạn có thể click đúp vào các node (hình tròn) để mở rộng thêm các kết nối của chúng.

## 2. Lọc Graph của Customer theo hành động cụ thể (ví dụ: chỉ xem đồ đã mua)
Nếu bạn chỉ muốn xem các sản phẩm mà `customer1` đã thực sự mua (không tính xem hay thêm vào giỏ hàng):

```cypher
MATCH (u:User {id: '1'})-[r:INTERACTS_WITH {action: 'purchase'}]->(p:Product)
RETURN u, r, p
```
Các action khác bạn có thể thay thế: `'view'`, `'cart'`.

## 3. Xem lịch sử tương tác của Customer (dạng bảng timeline)
Thay vì xem dạng Graph, bạn có thể xem dạng bảng thống kê các tương tác gần nhất của user để dễ đọc hơn:

```cypher
MATCH (u:User {id: '1'})-[r:INTERACTS_WITH]->(p:Product)
RETURN p.id AS product_id, r.action AS action, r.count AS so_lan_tuong_tac, r.last_ts AS thoi_gian_gan_nhat
ORDER BY r.last_ts DESC
LIMIT 50;
```

## 4. Xem chi tiết thông tin một Sản phẩm (Product)
Nếu bạn muốn kiểm tra xem một sản phẩm cụ thể đang được kết nối với những user nào (ai đã mua/xem nó):

```cypher
MATCH (u:User)-[r:INTERACTS_WITH]->(p:Product {id: '1'})
RETURN u, r, p
```

## 5. Xem top các Sản phẩm bán chạy nhất trong hệ thống
Lệnh này giúp bạn biết sản phẩm nào đang hot nhất dựa trên tổng số lượt mua:

```cypher
MATCH (:User)-[r:INTERACTS_WITH {action: 'purchase'}]->(p:Product)
RETURN p.id AS product_id, sum(r.count) AS tong_luot_mua
ORDER BY tong_luot_mua DESC
LIMIT 10;
```

## 6. Gợi ý sản phẩm cơ bản bằng Graph (Collaborative Filtering)
Nếu bạn muốn demo cách Graph Database có thể đưa ra gợi ý: "Những người giống bạn (cùng mua sản phẩm A) cũng đã mua sản phẩm B".
Ví dụ cho `customer1`:

```cypher
// Tìm những người đã tương tác với cùng sản phẩm như customer1,
// sau đó xem họ tương tác với sản phẩm nào khác mà customer1 chưa biết đến.
MATCH (u:User {id: '1'})-[:INTERACTS_WITH]->(p1:Product)<-[:INTERACTS_WITH]-(other:User)-[:INTERACTS_WITH]->(p2:Product)
WHERE NOT (u)-[:INTERACTS_WITH]->(p2)
RETURN p2.id AS product_goi_y, count(other) AS do_pho_bien
ORDER BY do_pho_bien DESC
LIMIT 5;
```

## 7. Xem tổng quan toàn bộ Graph (Giới hạn số lượng)
Nếu bạn muốn show một graph tổng quan đẹp mắt chứa nhiều user và product (giới hạn 100 node để tránh treo trình duyệt):

```cypher
MATCH (n)-[r]->(m)
RETURN n, r, m
LIMIT 100
```

## 8. Xoá toàn bộ dữ liệu (Chỉ dùng khi cần reset)
**CẢNH BÁO**: Lệnh này sẽ xoá toàn bộ node và relationship trong database.
```cypher
MATCH (n) DETACH DELETE n
```
