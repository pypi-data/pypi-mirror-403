def get_all_code():
    """
    Возвращает весь твой код как одну строку
    """
    code_text = """docker ---------------------------

docker-compose up -d

# Остановить  
docker-compose down

# Пересобрать и запустить
docker-compose up -d --build

# Перезапустить
docker-compose restart

# Показать контейнеры
docker-compose ps

# Логи
docker-compose logs api

# yml
"
services:
  db:
    image: mysql:8.0
    ports:
      - "3307:3306"
    environment:
      MYSQL_ROOT_PASSWORD: qwe123
      MYSQL_DATABASE: Bib
  api:
    build: .
    depends_on:
      - db
    ports:
      - "3000:8080"
    environment:
      DBHOST: db
      ASPNETCORE_ENVIRONMENT: Development
"



mysql-----------------------------------------------------
Scaffold-DbContext "Server=localhost;Port=3306;Database=publishing;User=root;Password=8989;" 
Pomelo.EntityFrameworkCore.MySql -OutputDir Model


програ--------------------------------------------------------------------------------------
1 контекст
optionsBuilder.UseMySql("server=host.docker.internal;port=3306;
database=auth_system;user=root;password=qwe123",
 Microsoft.EntityFrameworkCore.ServerVersion.Parse("9.5.0-mysql"));

2 програм кс

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();


builder.Services.AddCors(options =>
{
    options.AddPolicy("AllowAll", policy =>
    {
        policy.AllowAnyOrigin()
              .AllowAnyMethod()
              .AllowAnyHeader();
    });
});

var app = builder.Build();


app.UseSwagger();
app.UseSwaggerUI();

app.UseCors("AllowAll"); 



app.UseAuthorization();
app.MapControllers();
app.Run();



3 NewsClass
using Microsoft.EntityFrameworkCore;

namespace WebApplication5.Model
{
    public class NewsClass
    {
        AuthSystemContext context = new AuthSystemContext();

        public List<User> GetUsers()
        {
            return context.Users.ToList();
        }

        public void AddUsers(User user)
        {
            context.Users.Add(user);
            context.SaveChanges();
        }

        public List<Novo> GetNews()
        {
            return context.Novos.ToList();
        }

        public void AddNews(Novo news)
        {
            context.Novos.Add(news);
            context.SaveChanges();
        }
    }
}




4 контроллер
using Microsoft.AspNetCore.Mvc;
using WebApplication5.Model;

namespace WebApplication5.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class BibaController : ControllerBase 
    {
        NewsClass bib = new NewsClass();

        [HttpGet("GetUser")]
        public List<User> GetUsers()
        {
            return bib.GetUsers();
        }

        [HttpPost("AddUser")]
        public IActionResult AddUsers([FromBody] User user)
        {
            bib.AddUsers(user);
            return Ok();
        }


        [HttpGet("GetNews")]
        public List<Novo> GetNews()
        {
            return bib.GetNews();
        }

        [HttpPost("AddNews")]
        public IActionResult AddNews([FromBody] Novo news)
        {
            bib.AddNews(news);
            return Ok();
        }
    }
}


5 кс жопа

<Project Sdk="Microsoft.NET.Sdk.Web">
  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
    <Nullable>enable</Nullable>
    <ImplicitUsings>enable</ImplicitUsings>
    <GenerateDocumentationFile>true</GenerateDocumentationFile>
    <NoWarn>$(NoWarn);1591</NoWarn>
    <UserSecretsId>0128433f-6b6c-4fbe-8a71-9e703d2009eb</UserSecretsId>
    <DockerDefaultTargetOS>Linux</DockerDefaultTargetOS>
  </PropertyGroup>

  <ItemGroup>
    <PackageReference Include="Microsoft.EntityFrameworkCore" Version="8.0.0" />
    <PackageReference Include="Microsoft.EntityFrameworkCore.Tools" Version="8.0.0">
      <PrivateAssets>all</PrivateAssets>
      <IncludeAssets>runtime; build; native; contentfiles; analyzers; buildtransitive</IncludeAssets>
    </PackageReference>
    <PackageReference Include="Pomelo.EntityFrameworkCore.MySql" Version="8.0.0" />
    <PackageReference Include="Swashbuckle.AspNetCore" Version="6.6.2" />
    <PackageReference Include="Microsoft.AspNetCore.OpenApi" Version="8.0.0" />
  </ItemGroup>
</Project>





WPF ---------------------------------------------------------------------------------------------------------------------------

MAIN WINDOW 


using System;
using System.Net.Http;
using System.Windows;


namespace WpfApp5
{

    public partial class MainWindow : Window
    {
        public MainWindow()
        {
            InitializeComponent();
        }

        private async void Login_Click(object sender, RoutedEventArgs e)
        {
            string user = txtUser.Text;
            string pass = txtPass.Password;

            try
            {
                using (HttpClient client = new HttpClient())
                {

                    string response = await client.GetStringAsync("http://localhost:3000/api/Biba/GetUser");

                    if (response.Contains($"\"username\":\"{user}\"") &&
                        response.Contains($"\"password\":\"{pass}\""))
                    {
                        new NewsWindow().Show();
                        this.Close();
                    }
                    else
                    {
                        txtError.Text = "Неверные данные";
                    }
                }
            }
            catch (Exception ex)
            {
                txtError.Text = ex.Message;
            }
        }
    }
}


<Window x:Class="WpfApp5.MainWindow"
        xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
        xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
        xmlns:d="http://schemas.microsoft.com/expression/blend/2008"
        xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006"
        xmlns:local="clr-namespace:WpfApp5"
        mc:Ignorable="d"
        Title="MainWindow" Height="450" Width="800">
    <Grid>
        <StackPanel Margin="20" VerticalAlignment="Center">
            <TextBlock Text="Вход" FontSize="20" Margin="0,0,0,10"/>

            <TextBlock Text="Логин:"/>
            <TextBox x:Name="txtUser" Margin="0,5,0,10"/>

            <TextBlock Text="Пароль:"/>
            <PasswordBox x:Name="txtPass" Margin="0,5,0,20"/>

            <Button Content="Войти" Click="Login_Click" Height="30"/>
            <TextBlock x:Name="txtError" Foreground="Red" Margin="0,10,0,0"/>
        </StackPanel>

    </Grid>
</Window>


NewsWindow

<Window x:Class="WpfApp5.NewsWindow"
        xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
        xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
        xmlns:d="http://schemas.microsoft.com/expression/blend/2008"
        xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006"
        xmlns:local="clr-namespace:WpfApp5"
        mc:Ignorable="d"
        Title="NewsWindow" Height="450" Width="800">
    <Grid>
        <DataGrid x:Name="dgNews" Margin="10"/>
    </Grid>
</Window>





using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Text.Json;
using System.Windows;

namespace WpfApp5
{
    public partial class NewsWindow : Window
    {
        public NewsWindow()
        {
            InitializeComponent();
            LoadNews();
        }

        private async void LoadNews()
        {
            try
            {
                using (HttpClient client = new HttpClient())
                {
                    string json = await client.GetStringAsync("http://localhost:3000/api/Biba/GetNews");

                    var newsList = ParseNewsJson(json);
                    dgNews.ItemsSource = newsList;

                }
            }
            catch (Exception ex)
            {
                MessageBox.Show("Ошибка: " + ex.Message);
            }
        }

        private List<NewsItem> ParseNewsJson(string json)
        {
            var newsList = new List<NewsItem>();
            try
            {
                using (JsonDocument doc = JsonDocument.Parse(json))
                {
                    foreach (var item in doc.RootElement.EnumerateArray())
                    {
                        var news = new NewsItem
                        {
                            Id = item.TryGetProperty("id", out var idProp) ? idProp.GetInt32() : 0,
                            Title = item.TryGetProperty("title", out var titleProp) ? titleProp.GetString() : "",
                            Opisnie = item.TryGetProperty("opisnie", out var opisProp) ? opisProp.GetString() : "",

                        };
                        newsList.Add(news);
                    }
                }
            }
            catch
            {

            }

            return newsList;
        }
    }


    public class NewsItem
    {
        public int Id { get; set; }
        public string Title { get; set; }
        public string Opisnie { get; set; }

    }
}"""

    return code_text