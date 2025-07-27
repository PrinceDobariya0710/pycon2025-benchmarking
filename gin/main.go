package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"strconv"

	"github.com/gin-gonic/gin"
	"github.com/joho/godotenv"
	"gorm.io/driver/postgres"
	"gorm.io/gorm"
)

type Product struct {
	ID          uint    `gorm:"column:id;primaryKey;index" json:"id"`
	Name        string  `gorm:"column:name;type:varchar" json:"name"`
	Description string  `gorm:"column:description;type:text" json:"description"`
	Brand       string  `gorm:"column:brand;type:varchar" json:"brand"`
	Category    string  `gorm:"column:category;type:varchar" json:"category"`
	Price       float64 `gorm:"column:price;type:numeric" json:"price"`
	Currency    string  `gorm:"column:currency;type:varchar" json:"currency"`
	Stock       int     `gorm:"column:stock;type:integer" json:"stock"`
	EAN         string  `gorm:"column:ean;type:varchar" json:"ean"`
	Color       string  `gorm:"column:color;type:varchar" json:"color"`
	Size        string  `gorm:"column:size;type:varchar" json:"size"`
	Availability string `gorm:"column:availability;type:varchar" json:"availability"`
	InternalID   string `gorm:"column:internal_id;type:varchar" json:"internal_id"`
}

func (Product) TableName() string {
	return "product" // Matches FastAPI's __tablename__ = "product"
}

func getEnv(key, fallback string) string {
	if value, ok := os.LookupEnv(key); ok {
		return value
	}
	return fallback
}

func setupDB() *gorm.DB {
	_ = godotenv.Load()
	host := getEnv("POSTGRES_HOST", "localhost")
	port := getEnv("POSTGRES_PORT", "5432")
	user := getEnv("POSTGRES_USER", "postgres")
	password := getEnv("POSTGRES_PASSWORD", "root")
	dbname := getEnv("POSTGRES_DB", "benchmark_db")
	dsn := fmt.Sprintf("host=%s port=%s user=%s password=%s dbname=%s sslmode=disable", host, port, user, password, dbname)
	db, err := gorm.Open(postgres.Open(dsn), &gorm.Config{
		DisableForeignKeyConstraintWhenMigrating: true,
	})
	if err != nil {
		log.Fatalf("failed to connect database: %v", err)
	}

	// Drop and recreate the table
	if db.Migrator().HasTable(&Product{}) {
		if err := db.Migrator().DropTable(&Product{}); err != nil {
			log.Fatalf("failed to drop table: %v", err)
		}
	}

	// Create the table with the correct schema
	if err := db.AutoMigrate(&Product{}); err != nil {
		log.Fatalf("failed to migrate: %v", err)
	}
	return db
}

func main() {
	db := setupDB()
	r := gin.Default()
	r.LoadHTMLGlob("templates/*")

	r.GET("/plain-text", func(c *gin.Context) {
		c.Data(http.StatusOK, "text/plain; charset=utf-8", []byte("Hello, world!"))
	})

	r.GET("/json", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{"message": "Hello, world from JSON serialization endpoint!"})
	})

	r.POST("/products", func(c *gin.Context) {
		var product Product
		var raw map[string]interface{}
		if err := c.ShouldBindJSON(&raw); err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
			return
		}
		// Coerce price and stock
		if v, ok := raw["price"]; ok {
			switch val := v.(type) {
			case string:
				f, err := strconv.ParseFloat(val, 64)
				if err == nil {
					product.Price = f
				}
			case float64:
				product.Price = val
			}
		}
		if v, ok := raw["stock"]; ok {
			switch val := v.(type) {
			case string:
				i, err := strconv.Atoi(val)
				if err == nil {
					product.Stock = i
				}
			case float64:
				product.Stock = int(val)
			}
		}
		b, _ := json.Marshal(raw)
		_ = json.Unmarshal(b, &product)
		if err := db.Create(&product).Error; err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}
		c.JSON(http.StatusCreated, product)
	})

	r.GET("/products/:id", func(c *gin.Context) {
		id := c.Param("id")
		var product Product
		if err := db.First(&product, id).Error; err != nil {
			c.JSON(http.StatusNotFound, gin.H{"error": "Product not found"})
			return
		}
		c.JSON(http.StatusOK, product)
	})

	r.GET("/products", func(c *gin.Context) {
		limit, _ := strconv.Atoi(c.DefaultQuery("limit", "100"))
		offset, _ := strconv.Atoi(c.DefaultQuery("offset", "0"))
		var products []Product
		if err := db.Limit(limit).Offset(offset).Find(&products).Error; err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}
		c.JSON(http.StatusOK, products)
	})

	r.PUT("/products/:id", func(c *gin.Context) {
		id := c.Param("id")
		var product Product
		if err := db.First(&product, id).Error; err != nil {
			c.JSON(http.StatusNotFound, gin.H{"error": "Product not found"})
			return
		}
		var raw map[string]interface{}
		if err := c.ShouldBindJSON(&raw); err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
			return
		}
		if v, ok := raw["price"]; ok {
			switch val := v.(type) {
			case string:
				f, err := strconv.ParseFloat(val, 64)
				if err == nil {
					raw["price"] = f
				}
			}
		}
		if v, ok := raw["stock"]; ok {
			switch val := v.(type) {
			case string:
				i, err := strconv.Atoi(val)
				if err == nil {
					raw["stock"] = i
				}
			}
		}
		db.Model(&product).Updates(raw)
		c.JSON(http.StatusOK, product)
	})

	r.DELETE("/products/:id", func(c *gin.Context) {
		id := c.Param("id")
		if err := db.Delete(&Product{}, id).Error; err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}
		c.JSON(http.StatusOK, gin.H{"ok": true})
	})

	r.GET("/fortune", func(c *gin.Context) {
		var products []Product
		db.Limit(100).Find(&products)
		c.HTML(http.StatusOK, "fortune.html", gin.H{"products": products})
	})

	port := getEnv("PORT", "8080")
	r.Run(":" + port)
}
