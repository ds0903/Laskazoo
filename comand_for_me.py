"""команди для бекапап бази а також підклчюення до сервера по ssh і взпшплі команди для сервера """
# TODO: команда аби імпортувати файл python manage.py loaddata /home/torgsoft/incoming/data.json --settings=Laskazoo.settings.prod
# TODO: команда аби забекапить базу python manage.py dumpdata --natural-foreign --natural-primary --indent 2 --output data.json
# TODO: команда аби перекинуть файл scp C:\ftp\torgsoft\incoming\data.json danil@laskazoo.com.ua:/home/torgsoft/incoming/
# TODO: підкчлючення до сервера ssh danil@178.158.244.87 source .venv/bin/activate source venv/bin/activate
# TODO: перезавантаженян сервера !!!
# python manage.py flush очистить базу на проді
# 1) бекенд (gunicorn або твій unit, наприклад laskazoo.service)
# sudo systemctl restart gunicorn        # якщо сервіс називається gunicorn
# # або
# sudo systemctl restart laskazoo        # якщо ти робив systemd unit laskazoo.service
#
# # 2) nginx
# sudo nginx -t && sudo systemctl reload nginx
#
# # 3) FTP (vsftpd)
# sudo systemctl restart vsftpd
# TODO: перезавантаженян статичних файлів !!!
# export DJANGO_SETTINGS_MODULE=Laskazoo.settings.prod
# python manage.py collectstatic --noinput
# ngrok http http://localhost:8080
# python manage.py import_tsgoods імпорт в базу з сервера
# python manage.py sync_ts_direct чинхронізація з сервером
