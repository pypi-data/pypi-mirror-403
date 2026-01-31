% include('templates/header.tpl')

<div id="review-table"></div>

<script src="https://cdn.jsdelivr.net/npm/luxon/build/global/luxon.min.js"></script>
<script type="text/javascript" src="https://unpkg.com/tabulator-tables@6.3.0/dist/js/tabulator.min.js"></script>
<script type="text/javascript">

var table = new Tabulator("#review-table", {
 	height:1525, // set height of table (in CSS or here), this enables the Virtual DOM and improves render speed dramatically (can be any valid css height value)
 	ajaxURL:"/json-results-data",
 	ajaxContentType:"json",
 	layout:"fitColumns", //fit columns to width of table (optional)
    autoColumns:true,
});

</script>

% include('templates/footer.tpl')
