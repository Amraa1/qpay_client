QPay Client-ийн гарын авлага
============================

**qpay-client** нь QPay v2 API-тай Python орчноос холбогдох ажлыг хялбарчлах клиент сан юм.
Энэ сан нь ``async`` болон ``sync`` хоёр төрлийн клиент, Pydantic schema-ууд, токен шинэчлэлт,
сүлжээний алдааны дахин оролдлого, мөн QPay-ийн нийтлэг endpoint-уудын typed wrapper-уудыг агуулдаг.

Энэхүү баримт бичиг нь Read the Docs дээр харагдах албан ёсны гарын авлага бөгөөд дараах зүйлсийг тайлбарлана:

- ``AsyncQPayClient`` болон ``QPayClient``-ийг хэрхэн ашиглах
- ``QPaySettings``-ийг sandbox болон production орчинд хэрхэн үүсгэх
- invoice, payment, ebarimt, subscription endpoint-уудтай хэрхэн ажиллах
- API reference-ийг хаанаас харах

.. toctree::
   :maxdepth: 2
   :caption: Агуулга

   overview
   quickstart
   examples
   api
   sync_api


