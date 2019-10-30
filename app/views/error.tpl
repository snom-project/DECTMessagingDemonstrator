% include('header.tpl', title='Page Title')
<div class="container">
    <div class="alert alert-danger" role="alert">
        <h2>Error in {{data['extension']}}:</h2>
        {{data['message']}}
    </div>
</div>
% include('footer.tpl')
