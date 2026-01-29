Kerttula
========

`Kerttula™` is a home automation application built on top of 'Juham™' framework.
It controls Juha's home.


Motivation
----------

Yes, existing home automation solutions exist — for example, Home Assistant.
I decided not to use any of them, because that would be incredibly boring.
Instead, I chose to build one from scratch, because it seemed like a much more exciting way to learn Python and the GitLab ecosystem.

It hasn’t been all fun, though.

Sphinx and its extremely fragile .rst syntax have haunted me from day one.
Python has tried to drive me crazy too — with its indentation-based structure, endless deprecations, random bugs, and the limitations of its type annotation system.

At several points I seriously regretted not writing everything in C/C++.
But in the end, I don’t regret anything.
Despite all the ups and downs, this project has been exactly what I needed to avoid wasting my spare time on something even more pointless.




Project Status
--------------

**Current State**: **Alpha (Status 3)**  
In its current form, Kerttula™ may still resemble more of a distant mission (or even a "mess") than a "masterpiece," but I'm actively developing it to reach that goal!

Please check out the `CHANGELOG <CHANGELOG.rst>`_ file for changes in this release.


Installation
------------

The installation is two stage process

1. To install:

.. code-block:: python

    pip install kerttula


2. Configure

   OpenWeatherMap and various other services require you to register and obtain web keys and things like
   that. Most importantly, Influx DB and Graphana cloud accounts must be created for data visualization.
   Please consult 'juham' documentation for more information.



License
-------

This project is licensed under the MIT License - see the `LICENSE <LICENSE.rst>`_ file.

