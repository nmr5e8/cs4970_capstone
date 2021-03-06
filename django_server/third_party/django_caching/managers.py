from django.db import models
from django.db.models import signals
from cache import cache
from django.db.models.query import QuerySet

CACHE_DURATION = 3600

def _cache_key(model, value, field=None, module_name=None):
    if not module_name:
        module_name = model._meta.module_name
        
    # It's safe to hot-swap a "deferred_poly" version of a PolyModel
    # for the non-deffered version. Django will just have to query again
    # for the poly.
    module_name = module_name.replace('_deferred_poly','')
    
    if field:
        return "%s:%s.%s:%s" % (model._meta.app_label, module_name, field, value)
    else:
        return "%s.%s:%s" % (model._meta.app_label, module_name, value)

def _get_cache_key(self, field=None, module_name=None):
    if field:
        return self._cache_key(getattr(self,field), field, module_name)
    else:
        return self._cache_key(self.pk)

class CachingManager(models.Manager):
    def __init__(self, use_for_related_fields=True, *args, **kwargs):
        self.use_for_related_fields = use_for_related_fields
        super(CachingManager, self).__init__(*args, **kwargs)

    def get_query_set(self):
        return CachingQuerySet(self.model)

    def contribute_to_class(self, model, name):
        signals.post_save.connect(self._post_save, sender=model)
        signals.post_delete.connect(self._post_delete, sender=model)
        setattr(model, '_cache_key', classmethod(_cache_key))
        setattr(model, '_get_cache_key', _get_cache_key)
        setattr(model, 'cache_key', property(_get_cache_key))
        return super(CachingManager, self).contribute_to_class(model, name)

    def _invalidate_cache(self, instance):
        """
        Explicitly set a None value instead of just deleting so we don't have any race
        conditions where:
            Thread 1 -> Cache miss, get object from DB
            Thread 2 -> Object saved, deleted from cache
            Thread 1 -> Store (stale) object fetched from DB in cache
        Five second should be more than enough time to prevent this from happening for
        a web app.
        """
        cache.set(instance.cache_key, None, 5)
        if hasattr(instance,'slug'):
            cache.set(instance._get_cache_key('slug'), None, CACHE_DURATION)

    def _post_save(self, instance, **kwargs):
        self._invalidate_cache(instance)

    def _post_delete(self, instance, **kwargs):
        self._invalidate_cache(instance)


class CachingQuerySet(QuerySet):
    def iterator(self):
        superiter = super(CachingQuerySet, self).iterator()
        while True:
            obj = superiter.next()
            # Use cache.add instead of cache.set to prevent race conditions (see CachingManager)
            cache.add(obj.cache_key, obj, CACHE_DURATION)
            if hasattr(obj,'slug'):
                cache.add(obj._get_cache_key('slug'), obj, CACHE_DURATION)
            yield obj
    
    def get(self, *args, **kwargs):
        """
        Checks the cache to see if there's a cached entry for this pk. If not, fetches 
        using super then stores the result in cache.

        Most of the logic here was gathered from a careful reading of 
        ``django.db.models.sql.query.add_filter``
        """
        if self.query.where:
            # If there is any other ``where`` filter on this QuerySet just call
            # super. There will be a where clause if this QuerySet has already
            # been filtered/cloned.
            return super(CachingQuerySet, self).get(*args, **kwargs)

        # Punt on anything more complicated than get by pk/id only...
        if len(kwargs) == 1:
            k = kwargs.keys()[0]
            obj = None
            if k in ('pk', 'pk__exact', '%s' % self.model._meta.pk.attname, 
                     '%s__exact' % self.model._meta.pk.attname):
                obj = cache.get(self.model._cache_key(
                    value=kwargs.values()[0],
                    module_name = self.model._meta.module_name
                ))
            elif k in ('slug','slug__iexact','slug__exact'):
                obj = cache.get(self.model._cache_key(
                    field="slug",
                    value=kwargs.values()[0],
                    module_name = self.model._meta.module_name
                ))
            if obj is not None:
                obj.from_cache = True
                return obj

        # Calls self.iterator to fetch objects, storing object in cache.
        return super(CachingQuerySet, self).get(*args, **kwargs)

# ------------------ custom code, adds support for geo: --------------------
from django.conf import settings
if ('django.contrib.gis' in settings.INSTALLED_APPS):
    from django.contrib.gis.db import models as geo_models

    class GeoCachingManager(geo_models.GeoManager):
        def __init__(self, use_for_related_fields=True, *args, **kwargs):
            self.use_for_related_fields = use_for_related_fields
            super(GeoCachingManager, self).__init__(*args, **kwargs)

        def get_query_set(self):
            return GeoCachingQuerySet(self.model)

        def contribute_to_class(self, model, name):
            signals.post_save.connect(self._post_save, sender=model)
            signals.post_delete.connect(self._post_delete, sender=model)
            setattr(model, '_cache_key', classmethod(_cache_key))
            setattr(model, '_get_cache_key', _get_cache_key)
            setattr(model, 'cache_key', property(_get_cache_key))
            return super(GeoCachingManager, self).contribute_to_class(model, name)

        def _invalidate_cache(self, instance):
            """
            Explicitly set a None value instead of just deleting so we don't have any race
            conditions where:
                Thread 1 -> Cache miss, get object from DB
                Thread 2 -> Object saved, deleted from cache
                Thread 1 -> Store (stale) object fetched from DB in cache
            Five second should be more than enough time to prevent this from happening for
            a web app.
            """
            cache.set(instance.cache_key, None, 5)
            if hasattr(instance,'slug'):
                cache.set(instance._get_cache_key('slug'), None, CACHE_DURATION)

        def _post_save(self, instance, **kwargs):
            self._invalidate_cache(instance)

        def _post_delete(self, instance, **kwargs):
            self._invalidate_cache(instance)

    class PolyDeferGeoManager(GeoCachingManager):
        """
        Same as above, but defers 'poly' fields. Split off
        because the .defer() method MUST only be called on the parent class.
        """
        def get_query_set(self):
			return GeoCachingQuerySet(self.model).defer('poly',)

    class GeoCachingQuerySet(geo_models.query.GeoQuerySet):
        def iterator(self):
            superiter = super(GeoCachingQuerySet, self).iterator()
            while True:
                obj = superiter.next()
                # Use cache.add instead of cache.set to prevent race conditions (see CachingManager)
                cache.add(obj.cache_key, obj, CACHE_DURATION)
                if hasattr(obj,'slug'):
                    cache.add(obj._get_cache_key('slug'), obj, CACHE_DURATION)
                yield obj

        def get(self, *args, **kwargs):
            """
            Checks the cache to see if there's a cached entry for this pk. If not, fetches 
            using super then stores the result in cache.

            Most of the logic here was gathered from a careful reading of 
            ``django.db.models.sql.query.add_filter``
            """
            if self.query.where:
                # If there is any other ``where`` filter on this QuerySet just call
                # super. There will be a where clause if this QuerySet has already
                # been filtered/cloned.
                return super(GeoCachingQuerySet, self).get(*args, **kwargs)

            # Punt on anything more complicated than get by pk/id only...
            if len(kwargs) == 1:
                k = kwargs.keys()[0]
                obj = None
                if k in ('pk', 'pk__exact', '%s' % self.model._meta.pk.attname, 
                         '%s__exact' % self.model._meta.pk.attname):
                    obj = cache.get(self.model._cache_key(
                        value=kwargs.values()[0],
                        module_name = self.model._meta.module_name
                    ))
                elif k in ('slug','slug__iexact','slug__exact'):
                    obj = cache.get(self.model._cache_key(
                        field="slug",
                        value=kwargs.values()[0],
                        module_name = self.model._meta.module_name
                    ))

                if obj is not None:
                    obj.from_cache = True
                    return obj

            # Calls self.iterator to fetch objects, storing object in cache.
            return super(GeoCachingQuerySet, self).get(*args, **kwargs)
