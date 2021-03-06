from base_handler import Handler
from models.page import Content, Page, Section
from models.auth import User, Role, Permission
from models.theme import ThemePackage, Theme
from models.site import  Site, Image
from google.appengine.ext.webapp import template
from google.appengine.api import memcache
from google.appengine.ext import db
import logging
from utility import user_import, email_notifier
from utility.cache import Cache

ACTIONS = ['view', 'edit']
def admin(handler_method):
  """ Admin required decorator
  """
  def redirect_if_needed(self, *args, **kwargs):
    user = self.ws.users.get_current_user(self)
    if user == None:
      self.redirect(self.ws.users.create_login_url('/admin'))
    else:
      is_admin = self.ws.users.is_current_user_admin(self)
      if(is_admin):
        handler_method(self, *args, **kwargs)
      else:
        self.redirect("/")
  return redirect_if_needed

class Admin():
  class Install(Handler):
    def get(self):
      site = Site.all().get()
      if(site):
        self.redirect("/")
      self.render_out("templates/install.html")
    def post(self):
      site = Site.all().get()
      if(site):
        self.redirect("/")
      save_items = {'site.title':'','site.admin':'','site.password':''}
      form_items = ['site.title','site.admin','site.password']
      for item in form_items:
        if item in self.request.arguments():
          if self.request.get(item) != "":
            save_items[item] = self.request.get(item)
          else:
            self.json_out({"success":False,"message":"%s is not entered" % item})
            return False
        else:
          self.json_out({"success":False,"message":"%s is not in the form" % item})
          return False
      user = self.ws.users.get_current_user(self)
      site = Site.create(save_items['site.admin'],save_items['site.password'],save_items['site.title'],user)
      self.redirect('/')

  class Administrate(Handler):
    @admin
    def get(self):
      contents = Content.all().fetch(1000)
      theme_packages = ThemePackage.all().fetch(1000)
      themes = Theme.all().fetch(1000)
      pages = Page.all().fetch(1000)
      images = Image.all().fetch(1000)
      roles = Role.all().fetch(1000)
      sections = Section.all().fetch(1000)
      _users = User.all().fetch(1000)
      actions = ACTIONS
      template_values = {'logout_url':self.ws.users.create_logout_url('/'),'theme_packages': theme_packages,'themes': themes, 'images': images, 'pages': pages, 'contents':contents, 'roles':roles, 'users':_users, 'actions': actions, 'sections': sections, 'site': self.ws.site}
      self.response.out.write(template.render('templates/manage.html',template_values))

  class CacheClear(Handler):
    @admin
    def get(self):
      self.response.out.write(memcache.flush_all())

  class AddItem(Handler):
    @admin
    def get(self, type, format):
      if type.capitalize() in globals():
        cls = globals()[type.capitalize()]
        if cls:
          self.response.out.write(cls.to_form("/"))
    @admin
    def post(self, type, format):
      if type.capitalize() in globals():
        cls = globals()[type.capitalize()]
        if cls:
          values = {}
          for k in self.request.arguments():
            value = self.request.get_all(k)
            if k.split('-')[-1] == "permissions":
              values[k.split('-')[-1]] = ",".join(self.request.get_all("page.permissions"))
            if k.split('-')[-1] in cls().properties() and "List" in cls().properties()[k.split('-')[-1]].__class__().__str__():
              values[k.split('-')[-1]] = [x.lstrip().rstrip() for x in value]
            else:
              values[k.split('-')[-1]] = value
            values[k] = self.request.get(k)
          result = cls.create(values)
          if result:
            memcache.flush_all()
            if format == 'html':
              self.redirect(self.request.get("return_url"))
            elif format == 'json':
              self.json_out(result)
          else:
            self.response.out.write("Failed to update")
        else:
          self.response.out.write(self.request.get("return_url"))

  class EditItem(Handler):
    #TODO: finish dynamic form builder
    @admin
    def get(self, args, format):
      type = args.split("/")[0]
      key = args.split("/")[1]
      return_url = self.request.get("return_url")
      if type.capitalize() in globals():
        cls = globals()[type.capitalize()]
        if cls:
          self.response.out.write(cls.to_form(return_url, "edit", key))

    @admin
    def post(self, args, format):
      type = args.split("/")[0]
      key = args.split("/")[1].split("?")[0]
      if type.capitalize() in globals():
        cls = globals()[type.capitalize()]
        if cls:
          values = {}
          values["key"] = key

          for k in self.request.arguments():
            logging.info(k)
            value = self.request.get_all(k)
            logging.info(value)
            if k.split('-')[-1] in cls().properties().keys():
              if ".ListProperty" in cls().properties()[k.split('-')[-1]].__class__.__str__(""):
                if k.split("-")[-1] == "permissions":
                  values[k.split('-')[-1]] = self.request.get_all(k)
                else:
                  values[k.split('-')[-1]] = [x.lstrip().rstrip() for x in value.split(",")]
              else:
                values[k.split('-')[-1]] = value
            values[k] = self.request.get_all(k)
          result = cls.update(values)
          if result:
            memcache.flush_all()
            if format == 'html':
              self.redirect(self.request.get("return_url"))
            elif format == 'json':
              self.json_out(result)
          else:
            self.response.out.write("Failed to update")
        else:
          self.response.out.write(self.request.get("return_url"))

  class SetUserRoles(Handler):
    @admin
    def get(self, key=None, format=None):
      logging.info(key)
      logging.info(format)
      return_url = self.request.get('return_url')
      duser = db.get(key)
      self.response.out.write(duser.create_roles_form(return_url))
    @admin
    def post(self):
      user = self.request.get('user')
      role = self.request.get('role')
      return_url = self.request.get('return_url')
      if not user or not role:
        self.redirect(return_url)
      duser = db.get(user)
      drole = db.get(role)
      urole = duser.roles()
      for ur in urole:
        ur.users.remove(duser.key())
        ur.put()
      drole.users.append(duser.key())
      drole.put()
      memcache.flush_all()
      self.redirect(return_url)

  class DeleteItem(Handler):
    @admin
    def get(self, args, format):
      type = args.split("/")[0]
      key = args.split("/")[1]
      model = db.get(key)
      result = model.delete()
      self.ws.site.sanity_check()
      for role in Role.all().fetch(1000):
        role.sanity_check()
      for permission in Permission.all().fetch(1000):
        permission.sanity_check()
      memcache.flush_all()
      self.response.out.write(type + " : " + key)

  class ExportItem(Handler):
    @admin
    def get(self, args):
      array_args = args.split("/")
      key = array_args[1]
      self.json_out(Site.export(key))

  class EmailContent(Handler):
    @admin
    def post(self, *args):
      content = db.get(self.request.get('content'))
      role = db.get(self.request.get('role'))
      mailusers = db.get(role.users)
      result = email_notifier.EmailNotifier.notify(to = mailusers, sender='admin@iaos.net', content = content)
      if result:
        self.redirect('/')
      else:
        self.redirect('/admin/email/failure')

  class ImportItem(Handler):
    @admin
    def post(self, type):
      if type.lower() == 'users':
        csv_content = self.request.get('csv')
        self.json_out(user_import.UserCsv().read(csv_content))
      else:
        self.json_out({"error" : "Unsupported method"})

  class ListJavascript(Handler):
    @admin
    def get(self, type):
      if type == "images":
        self.response.headers.add_header("Content-Type","text/javascript")
        self.response.out.write("var tinyMCEImageList = [%s]" % "".join(["['" + image.title + "','" + image.to_url() +"']" for image in db.get(self.ws.site.images)]))
