<!doctype html>
<html lang="en">
  <head>
    <title>{{ 'Snom Messaging' }}</title>

    <!-- Required meta tags -->
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">

    <!-- alarm and sms selector needs these -->
    <link rel="stylesheet" type="text/css" href="/css/icon_font.css" />
    <link rel="stylesheet" type="text/css" href="css/jquery.transfer.css" />
    
    <!-- Bootstrap CSS -->
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css" integrity="sha384-Gn5384xqQ1aoWXA+058RXPxPg6fy4IWvTNh0E263XmFcJlSAwiGgFAW/dAiS6JXm" crossorigin="anonymous"> 

    <!-- cannot do 
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.0/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-gH2yIJqKdNHPEq0n4Mqa/HGKIhSkIHeL5AyhkYV8i59U5AR6csBvApHHNl/vI1Bx" crossorigin="anonymous"> 
    -->

    <!-- AutoRefresher (required)-->
    <link rel="stylesheet" href="css/autorefresher/css/autorefresher.min.css">    
  </head>

  <body>

    <link rel="stylesheet" href="css/styles.css">

    <!-- Optional JavaScript -->
    <!-- jQuery first, then Popper.js, then Bootstrap JS 
    <!--
    <script src="https://code.jquery.com/jquery-3.2.1.slim.min.js" integrity="sha384-KJ3o2DKtIkvYIK3UENzmM7KCkRr/rE9/Qpg6aAZGJwFDMVNA/GpGFF93hXpG5KkN" crossorigin="anonymous"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.12.9/umd/popper.min.js" integrity="sha384-ApNbgh9B+Y1QKtv3Rn7W3mgPxhU9K/ScQsAP7hUibX39j7fakFPskvXusvfa0b4Q" crossorigin="anonymous"></script>
    <script src="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/js/bootstrap.min.js" integrity="sha384-JZR6Spejh4U02d8jOt6vLEHfe/JQGiRRSQQxSfFWpi1MquVdAyjUar5+76PVCmYl" crossorigin="anonymous"></script>
    -->

    <script type="text/javascript"
        src="http://code.jquery.com/jquery-1.10.1.min.js">
    </script>
        
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.2.0/dist/js/bootstrap.min.js" integrity="sha384-ODmDIVzN+pFdexxHEHFBQH3/9/vQ9uori45z4JjnFsRydbmQbmL5t1tQ0culUzyK" crossorigin="anonymous"></script>
    <script src="https://cdn.jsdelivr.net/npm/@popperjs/core@2.11.5/dist/umd/popper.min.js" integrity="sha384-Xe+8cL9oJa6tN/veChSP7q+mnSPaj5Bcu9mPX5F5xIGE0DVittaqT5lorf0EI7Vk" crossorigin="anonymous"></script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.2.0/dist/js/bootstrap.bundle.min.js" integrity="sha384-A3rJD856KowSb7dwlZdYEkO39Gagi7vIsF0jrRAoQmDKKtQBHUuLZ9AsSv4jD4Xa" crossorigin="anonymous"></script>


    <script src="css/autorefresher/js/autorefresher.js"></script>

      <link rel="stylesheet" href="css/autorefresher/css/autorefresher.min.css">
      <script src="css/autorefresher/js/autorefresher.js"></script>


      <div class="d-flex flex-column flex-md-row align-items-center p-3 px-md-4 mb-3 bg-white border-bottom shadow-sm">
    <h5 class="my-0 mr-md-auto font-weight-normal"><a href="/"><img height="40px" src="/images/snom_logo_gray_60.png"></a></h5>
    <nav class="my-2 my-md-0 mr-md-3">
    <a class="p-2 text-dark" href="#">{{_('Features')}}</a>
    <a class="p-2 text-dark" href="#"> </a>
    <a class="p-2 text-dark" href="https://service.snom.com">{{_('Support')}}</a>
    <a class="p-2 text-dark" href="https://www.snom.com/partner/partner-portal/">{{_('Pricing')}}</a>
    </nav>



    <button class="btn btn-outline-secondary dropdown-toggle" type="button" id="dropdownMenuButton" data-bs-toggle="dropdown" aria-haspopup="true" aria-expanded="true">
      {{_('Select Language')}}
    </button>&nbsp;

    <div class="dropdown-menu" aria-labelledby="dropdownMenuButton">
      <a class="dropdown-item" href="/de_DE/"><img width="13%" src="/images/de_de.png"/> {{_('Deutsch')}}</a>
      <a class="dropdown-item" href="/en_US/"><img width="13%" src="/images/en_us.png"/> {{_('English')}}</a>
    </div>

    {{ session['profile_firstname']}} {{session['profile_lastname'] }}
    {% if session['profile_firstname'] != 'NA' %}
    {% set logonofftxt = 'Logoff' %}
    {% else %}
    {% set logonofftxt = 'Login' %}
    {% endif %}
    <a class="btn btn-outline-primary" href="/login">{{logonofftxt}}</a>

    </div>
