---
layout: page
permalink: /categories/
title: Tags
---

{%- comment -%} Sort tags by number of posts (most first), then alphabetically. {%- endcomment -%}
{%- capture tag_keys -%}
{%- for category in site.categories -%}
{%- assign n = category[1].size | plus: 1000 -%}{{ 2000 | minus: n }}|{{ category[0] }}{% unless forloop.last %},{% endunless %}
{%- endfor -%}
{%- endcapture -%}
{%- assign tag_keys = tag_keys | split: "," | sort -%}

<nav class="tag-cloud" aria-label="All tags">
{%- for key in tag_keys -%}
  {%- assign name = key | split: "|" | last -%}
  <a href="#{{ name | slugize }}">{{ name }} <span>{{ site.categories[name].size }}</span></a>
{%- endfor -%}
</nav>

{% for key in tag_keys %}
{%- assign name = key | split: "|" | last -%}
<section class="tag-group" id="{{ name | slugize }}">
  <h2 class="tag-group__title">{{ name }} <span>{{ site.categories[name].size }} {% if site.categories[name].size == 1 %}post{% else %}posts{% endif %}</span></h2>
  <ul class="tag-group__list">
    {%- for post in site.categories[name] -%}
    <li>
      <time datetime="{{ post.date | date_to_xmlschema }}">{{ post.date | date: "%b %Y" }}</time>
      <a href="{{ site.baseurl }}{{ post.url }}">{% if post.title and post.title != "" %}{{ post.title }}{% else %}{{ post.excerpt | strip_html }}{% endif %}</a>
    </li>
    {%- endfor -%}
  </ul>
</section>
{% endfor %}
