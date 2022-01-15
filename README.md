# Marketing Pipeline
Проект позволяет автоматизировать процесс маркетинговой аналитики.
Реализован сбор данных из рекламных кабинетов наиболее популярных в настоящий момент площадок:

:white_check_mark: Facebook

:white_check_mark: TikTok

:white_check_mark: Snapchat

## Оглавление

1. [Коротко о проекте](#Коротко-о-проекте)
2. [Как получить все нужные реквизиты для работы](#Как-получить-все-нужные-реквизиты-для-работы)
    - [Facebook](#Facebook)
    - [TikTok](#TikTok)
    - [Snapchat](#Snapchat)
    - [Google](#Google)
        1. [Google Sheets](#Google-Sheets)
        2. [Google Analytics](#Google-Analytics)
    - [Tableau](#Tableau)
3. [Как запустить проект](#Как-запустить-проект)
    - [Linux](#Linux)
    - [Windows](#Windows)
4. [Вывод программы](#Вывод-программы)
5. [Визуализация работы](#Визуализация-работы)
6. [Полезные ссылки](#Полезные-ссылки)

    
## Коротко о проекте

Проект направлен на решение реальной бизнес потребности: команда маркетинга любой сколь угодно крупной компании ежедневно сталкивается с проблемой анализа эффективности собственной рекламы. Бесплатных инструментов, позволяющих с легкостью анализировать на ежедневной основе данные о затраченных бюджетах и целевых конверсиях фактически не существует, с некоторыми оговорками можно попробовать использовать бесплатную версию аддона [Adveronix](https://workspace.google.com/marketplace/app/adveronix/523964251627) для Google Sheets, но из-за функциональной ограниченности бесплатной версии, вы быстро поймете, что настроенный процесс не особо масштабируем, и вам потребуется более гибкий, надежный и безопасный инструмент.

Представленный проект блестяще решает поставленную задачу, создавая сквозной поток данных из рекламных кабинетов в вашу внутреннюю базу данных, на основе чего можно настроить удобную визуализацию и позволить ежедневно команде маркетинга принимать бизнес решения, основанные на данных в несколько кликов.

Очевидно, что так как проект является b2b решением, нельзя просто скопировать репозиторий к себе. Изначально потребуется поработать с целью получения всех нужных доступов, создать простенькие приложения в каждом из рекламном кабинетов, которые позволят через OAuth 2.0 получить этому программному интерфейсу доступ к вашим данным.

Аналогично придется попотеть и с настройкой сервисных акканутов Google для создания возможно программно общаться с API Google Sheets и Google Analytics

[:arrow_up:Оглавление](#Оглавление)
___
## Как получить все нужные реквизиты для работы

### Facebook

Первое, что необходимо сделать для работы с Facebook API подтвердить акканут на Facebook. Когда это сделано, то у вас готов аккаунт разработчика и можно двигаться дальше — создать приложение. Для этого заходим в [Консоль разработчика Facebook](https://developers.facebook.com)
Далее `— «My Apps» — «Create App»`. Заполняем название приложения, контактный Email и жмём на `«Create App ID»`

Когда facebook ~~раздуплится~~ одобрит ваше приложение, вы сможете найти его там же, и рп клике на него перед вами откроется Dashboard приложения.
Переходим в `«Settings» — «Basic»` и записываем себе __App ID__ и __App Secret__. Эти данные понадобятся для авторизации.

Теперь переходим в `«Tools» — «Graph API Explorer»` и оказываемся в меню для создания нового `access token`.
Токены выдаются под разные нужды, и нам нужно задать определенные права для нашего. Нам потребуется два [ads_management](https://developers.facebook.com/docs/permissions/reference/ads_management/) и [ads_read](https://developers.facebook.com/docs/permissions/reference/ads_read/) — что позволяет каждый из них можно прочитать по ссылкам. Добавляем их и нажимаем на `«Generate Access Token»`.

Рекоммендую сразу нажать на голубой значок ℹ️ рядом с токеном, и проследовать по маршруту `«Open in Access Token Tool» — «Renew access token»` Чтобы продлить токен, в противном случае он будет недействителен через несолько часов. Сохраняем __Access Token__ и вписываем все сохраненные значения в соответствующие места, обозначенные как `<YOUR ...>`  программы `/scripts/AdsFacebook.py` и двигаемся дальше. Здесь самое сложное - ждать одобрения от Facebook, которое может произойти не очень быстро.

### TikTok

Здесь в целом похоже на Facebook, но есть свои тонкости, аналогично нужно иметь аккаунт (не путать с аккаунтом TikTok - его можно не иметь), внезапно авторизованный в требуемом рекламном аккануте. Далее переходим на сайт [TikTok Marketing API](https://ads.tiktok.com/marketing_api/homepage) и нажимаем `«Become a Developer»`.

Понеслась! Аккуратно, как и прежде, заполняем все формы, процесс создания аккаунта разработчика и приложения происходит совместно. Обратиет внимание на поле `callback-address`, туда требуется вписать адрес сайта вашей компании, к которому у вас есть доступ, это важно.

После одобрения приложения оно появится в списке под кнопкой `«My Apps»`. Переходим в приложение и сохраняем __App ID__ и __Secret__. После этого надо перейти по ссылке `«Advertiser authorization URL»`, авторизоваться с упомянутым выше аккаунтом, согласится на предоставление разрешений для приложения, подтвердить конопокой `«Confirm»`
Произойдет редирект на сайт, указанный в `callback-address` при создании приложения, обратите внимание на URL, там будет лежать заветный __auth_code__ - сохраните его.

Теперь вы готовы получить токен длительно доступа, для этого можно воспользоваться методом `get_tiktok_access_token` реализованным в `/scripts/AdsTikTok.py`, а можно сделать curl запрос:

```curl
curl -H "Content-Type:application/json" -X POST \
-d '{
    "secret": "SECRET", 
    "app_id": "APP_ID", 
    "auth_code": "AUTH_CODE"
}' \
https://ads.tiktok.com/open_api/v1.2/oauth2/access_token
```
Из полученного ответа сохраняем __access_token__ , вписываем его вместо `<YOUR ACCESS TOKEN>` в программе `/scripts/AdsTikTok.py` и идем разбираться со следующей платформой.

### Snapchat

Самый дружелюбный в настройке из всех рекламный кабинетов был оставлен "на сладкое". Здесь от вас потребуется минимум действий. 
Для начала уже привычно идем на соответствующий сайт [Snap Business Manager](https://business.snapchat.com/) и переходим в раздел `«Business Details»` 
Есть [документация](https://businesshelp.snapchat.com/s/article/api-apply?language=en_US) о коротких дальнейших действиях, главное - сохранить __Secret__ а также __Snap Client ID__ и __Snap Redirect URI__, но если последние два можно будет посмотреть на том же сайте после успешного создания приложение, то __Secret__ вы больше нигде не найдете, убедитесь, что сохранили его.  Кроме того  вам понадобится созранить __Organization ID__ он виден все в том же разделе `«Business Details»`. Впишите полученные четыре значения в соответствующие места, обозначенные как `<YOUR ...>`  программы `/scripts/AdsSnapchat.py`.\
Вы там увидите также поле __ad_account_id__, его трогать не надо. А вот поле __refresh_token__ заполнить надо обязательно, посредством выполнения метода `get_snapchat_refresh_token`, там потребуются уже записанные вами значения, следуйте указаниям и впишите полученное значение вместо `<YOUR REFRESH TOKEN>`

#### Google

История о взаимодействии с Google проще, здесь нет как таковой OAuth авторизации в отличие от подключения к рекламным кабинетам. Требуется создать просто два сервисных аккаунта (можно и один), посредством которых будет осуществляться сервер-серверное взаимодействие и аутентификация на программном уровне, используя доступы созданных роботов.

#### Google Sheets

Алгоритм простой: 
1. заходим в [Google Developers Console](https://console.developers.google.com/project) и создаем новый проект по кнопке `«Create Project»`
2. Посредством меню в левой части экрана переходим в раздел `«APIs & Services» — «Library»`, находим «Drive API» переходим и жмем `«Enable»`
3. Аналогично предыдущему пункту включаем `«Sheets API»`
4. Переходим теперь в раздел `«APIs & Services» — «Credentials»` и выбираем `«Create credentials» — «Service account key»`
5. Зполняем форму и подтверждаем посредством кнопки `«Create key»`
6. Выбираем из двух вариантов `«JSON»` и жмем `«Create»`
7. Скачанный файл переименовываем в transferbot.json и заменяем в корне этого проекта
8. Создаем новый Google Sheet, в который будет записываться все собранные данные по рекламе, и в доступах добавляем права редактора для __client_email__ из скачанного файла
9. Копируем из этого Google Sheet __spreadsheet_key__, он хранится в URL ```https://docs.google.com/spreadsheets/d/<spreadsheet_key>/edit#gid=...```
10. Скопированный на предыдущем шаге __spreadsheet_key__ вписываем вместо `<YOUR SPREADSHEET KEY>` в программе `/scripts/Marketing.py`

#### Google Analytics

Это требуется, чесли вы еще и собиираете данные через гугл аналитику и хотите оттуда так же получить какие-то показатели, реализовано по умолчанию - получение количества польовательских сессий. Здесь требууется практически то же, что и в предыдущем пункте, с небольшими изменениями

...
7. Скачанный файл переименовываем в gadatabot.json и заменяем в корне этого проекта
8. __client_email__ из скачанного файла вписываем в программе вместо `<YOUR CLIENT EMAIL>`
9. На сайте Google Analytics в разделе `«Admin» - «View»` копируем __View ID__ 
10. Скопированный на предыдущем шаге __View ID__ вписываем вместо `<YOUR VIEW ID>` в программе `/scripts/GoogleAnalytics.py`

### Tableau

В программе `/scripts/Marketing.py` реализовано обновление ноутбука в Tableau. Это имеет смысл для вас, если у вас есть сервер Tableau Server или Tableau Online на котором вы построили некоторую визуализацию, которую хотите обновлять по мере поступления новых данных. Если так, то заполните переменные `<YOUR ...>` со своими данными авторизации Tableau, введите домен и название вашего сайта, а также название ноутбука, который требуется обновлять.

[:arrow_up:Оглавление](#Оглавление)
___
## Как запустить проект

Ура! Вы готовы запрашивать данные из всех рекламных кабинетов. Складываются они по умолчанию в базу данных, права к которой хранятся в переменных окружения.
Итак, в зависимости от вашей операционной системы у вас есть разные возможности.

### Linux

У вас есть два способа запуска программы. Можно запустить bash-файл в терминале или использовать Docker контейнер для разворачивания в последствии, например, на виртуальной машине. В обоих случаях нужно скопировать репозиторий к себе на локальную машину и перейти в эту скачанную папку.

#### Запуск в терминале

```bash
export DB_HOST=<YOUR DATABASE>
export DB_USER=<YOUR USERNAME>
export DB_PWD=<YOUR PASSWORD>
RUN chmod a+x run.sh
./run.sh
```

#### Запуск через контейнер

Нужно заполнить поля `<YOUR DATABASE>`, `<YOUR USERNAME>` и `<YOUR PASSWORD>` в файле `Dockerfile`
После этого можно строить контейнер (единожды):
```bash
docker build -t <your docker nickname>/<image name> .
```
И запускать его:
```bash
docker run -p 8888:5000 <your docker nickname>/<image name>
```

Также для постановки кода на расписание можно положить вышеуказанную команду в файл `refresher.sh`. Потом выполнить:
```bash
chmod a+x refresher.sh
```
Убедиться, что файл стал исполняемым можно с помощи команды:
```bash
ls -lah
```
Потом выполнить команду и вписать а открывшийся файл строку из `cron.yaml`:
```bash
crontab -e
```
Убедится, что строка добавлена можно с помощью команды:
```bash
crontab -l
```

### Windows

Контейнер под Windows можно адаптировать самостоятельно, приведен способ запуска только через командную строку:

```cmd
set DB_HOST=<YOUR DATABASE>
set DB_USER=<YOUR USERNAME>
set DB_PWD=<YOUR PASSWORD>
.\run.bat
```

[:arrow_up:Оглавление](#Оглавление)
____
## Вывод программы

Вывод для каждой из операционных систем практически не отличается, для примера вот вывод в терминале Linux:

```bash
Marketing dashboard refreshing ...
Data upload success!
Getting Snapchat API access token...
Getting all accounts...
Getting all campaigns from Snapchat API...
Getting stats by each campaign from Snapchat API...
Getting stats by each campaign from Snapchat API...
Data upload success!
Data upload success!
Job 1 completed
Job 2 completed
Job 3 completed
Job 4 completed
Job 5 completed
Job 6 completed
Job 7 completed
Job 8 completed
Data upload success!
Data upload success!
Tableau workbook Marketing refreshed at 01/13/2022 06:17:15
Check /root/journal.log for more details.
```

[:arrow_up:Оглавление](#Оглавление)
____
## Визуализация работы

Мой процесс выстроен так, что код выполняется раз в сутки и сразу же обновляется дашборд в Tableau.
Команда маркетинга теперь ежедневно отслеживает аналитику рекламы через этот интерфейс. Выглядит примерно вот так:

![По всем каналам](https://user-images.githubusercontent.com/43523651/149632310-59f8ab21-8f0d-4265-bf6f-9a7d9e2ea186.png "All Channels")

![По каждому в отдельности](https://user-images.githubusercontent.com/43523651/149632328-78275db4-4a3f-4760-b220-e809fb6d7021.png "By Platforms")

[:arrow_up:Оглавление](#Оглавление)
____
## Полезные ссылки

1. [Facebook Graph API Explorer](https://developers.facebook.com/docs/graph-api/guides/explorer/)
2. [TikTok Marketing Api Docs](https://ads.tiktok.com/marketing_api/docs/)
3. [Snapchat Marketing Api Docs](https://marketingapi.snapchat.com/docs/)
4. [Google Analytics Api with Python](https://www.byperth.com/2017/06/11/google-analytics-api-python/)
5. [Connecting Tableau to Google Sheets](https://towardsdatascience.com/from-analysis-to-dashboarding-connecting-notebooks-to-tableau-483fa373f3a4)
6. [Habr Docker Tutorial](https://habr.com/ru/post/310460/)
7. [Habr TikTok Data Mining](https://habr.com/ru/company/ozontech/blog/562266/)
8. [About Adveronix](https://vc.ru/marketing/237297-kak-besplatno-eksportirovat-dannye-iz-reklamnyh-kabinetov-i-delat-avtomaticheskie-dashbordy-v-google-data-studio)

[:arrow_up:Оглавление](#Оглавление)
___
