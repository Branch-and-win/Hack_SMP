# 🚢 Приложение для планирования маршрутов ледоколов в СМП
Этот репозиторий содержит API для сервиса по планированию маршрутов атомных ледоколов по Северному морскому пути (СМП), разработанный командой Branch and Win.

## Функциональные возможности
### Сценарии
`create_scenario`
Создание сценария для планирования маршрутов.

**Описание**:
Позволяет создать сценарий, в котором можно задать различные входные данные для системы:

- Данные о заявках: дата начала заявки, класс проходимости;
- Данные об атомных ледоколах: их текущие местоположения и время начала работы, классы проходимости;
- Данные о портах, их местоположениях;
- Данные о графе перехода в СМП;
- Интегральная тяжесть льда в СМП (может быть сгенерирована с помощью `calculate_ice_integrality`).

- Параметры моделирования:

- - Дата начала построения расписания;
- - Количество дней планирования;
- - Количество дней сверх плана;
- - Количество лучших маршрутов для построения расписания.

`create_parent_scenario`
Создание родительского сценария, который выполняется последовательно интервалами времени, заданными в настройках сценария.

**Описание**:
Позволяет создать сценарий, в котором можно указать последнюю дату планирования, т.е. дату до которой будет осуществлен
последовательный расчет расписания.

`download_scenario`
Выгрузка входных и выходных данных сценария (если они есть).

### Моделирование
`calculate_scenario`
Запуск выбранного сценария для оптимизации расписания движения ледоколов по СМП.

`calculate_ice_integrality`
Запуск расчета тяжести льда. 

**Описание**:
Передаются данные о ледовой обстановке, данные о расположении портов, а также граф переходов в СМП.

## Отчет
После расчета сценария можно сформировать дашборд на основе выходных данных сценария. За формирование 
дашборда отвечает отдельный сервис `dash_app`, который реализует функционал загрузки результатов сценария для отображения отчета.

> Сценарий по умолчанию:
В системе загружен сценарий с названием base. Этот сценарий автоматически загружается при построении дашборда. Также можно выгрузить входные и выходные данные по нему.

## Установка и использование

Приложение реализовано в виде двух независимых сервисов: 
- `app` - сервис управления сценариями и моделирования;
- `dash_app` - сервис управления сценариями и моделирования. 

Оба сервиса обернуты в `Docker`, поэтому для запуска приложения необходимо установить на машину `Docker`
и иметь доступ в интернет.

После установки `Docker` выполните в корне следующую команду:
```commandline
docker-compose up -d
```

Дождитесь появления сообщения о локальном поднятии двух сервисов в контейнерах:
```commandline
Creating hack_smp_app_dash_1 ... done
Creating hack_smp_app_1      ... done
```

В результате чего будут доступны два сервиса по пути:

- `http://localhost:5021/docs` - API для работы со сценариями и запуском оптимизации;
- `http://localhost:5020/` - Дашборд с результатами работы (по умолчанию загружен сценарий `base`).
