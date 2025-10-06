"""команди для бекапап бази а також підклчюення до сервера по ssh і взпшплі команди для сервера """
# TODO: команда аби забекапить базу python manage.py dumpdata --natural-foreign --natural-primary --indent 2 --output data.json
# TODO: команда аби перекинуть файл scp C:\ftp\torgsoft\incoming\data.json danil@laskazoo.com.ua:/home/torgsoft/incoming/
# TODO: команда аби імпортувати файл python manage.py loaddata /home/torgsoft/incoming/data.json --settings=Laskazoo.settings.prod
# TODO: підкчлючення до сервера ssh danil@178.158.244.87 cd/srv/Laskazoo source .venv/bin/activate source venv/bin/activate
# TODO: перезавантаженян сервера !!!
# 7) Перезапуск gunicorn
# sudo systemctl daemon-reload
# sudo systemctl restart laskazoo
# python manage.py flush очистить базу на проді
# 1) бекенд (gunicorn або твій unit, наприклад laskazoo.service)
# sudo systemctl restart gunicorn        # якщо сервіс називається gunicorn
# # або
# sudo systemctl restart laskazoo        # якщо ти робив systemd unit laskazoo.service
# sudo nano /etc/systemd/system/laskazoo-sync.timer таймер як часто синхронізуємо товари
# # 2) nginx
# sudo nginx -t && sudo systemctl reload nginx
# sudo tail -n 30 /var/log/nginx/error.log
# # 3) FTP (vsftpd)
# sudo systemctl restart vsftpd
# TODO: перезавантаженян статичних файлів !!!
# export DJANGO_SETTINGS_MODULE=Laskazoo.settings.prod
# python manage.py collectstatic --noinput --settings=Laskazoo.settings.dev
# python manage.py collectstatic --noinput
# ngrok http http://localhost:8080
# python manage.py import_tsgoods імпорт в базу з сервера
# python manage.py sync_ts_direct чинхронізація з сервером
# запит фільтрація тих записів які вже є в нас
# DELETE FROM ts_goods
# WHERE good_id IN (
#     SELECT torgsoft_id FROM products_product
# )
# OR good_id IN (
#     SELECT torgsoft_id FROM products_product_variant
# );

# python manage.py setup_novaposhta