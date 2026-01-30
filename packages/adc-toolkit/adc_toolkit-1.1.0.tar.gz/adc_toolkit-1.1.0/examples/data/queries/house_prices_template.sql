SELECT
    Id,
    MSZoning,
    Neighborhood,
    CentralAir,
    added_at,
    SalePrice,
    LotArea
FROM `sample-project-351217.house_prices.train_data_date`
WHERE SalePrice >= {min_sales_price} AND LotArea >= {min_lot_area}
