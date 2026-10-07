SELECT CAST(make_date(source_year, source_month, 1) AS DATE) AS period, taxi, mean_duration FROM dashboard_monthly ORDER BY 1, 2;
