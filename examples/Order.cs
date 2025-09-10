using System;
using System.ComponentModel.DataAnnotations;

namespace ExampleProject.Core
{
    public class Order
    {
        public int Id { get; set; }
        
        [Required]
        public string OrderNumber { get; set; }
        
        public DateTime OrderDate { get; set; }
        public decimal TotalAmount { get; set; }
        public OrderStatus Status { get; set; }
        
        public int UserId { get; set; }
        public User User { get; set; }

        public Order()
        {
            OrderDate = DateTime.Now;
            Status = OrderStatus.Pending;
        }

        public Order(string orderNumber, decimal totalAmount) : this()
        {
            OrderNumber = orderNumber;
            TotalAmount = totalAmount;
        }

        public void MarkAsCompleted()
        {
            Status = OrderStatus.Completed;
        }

        public bool IsExpired()
        {
            return OrderDate.AddDays(30) < DateTime.Now;
        }
    }

    public enum OrderStatus
    {
        Pending,
        Processing,
        Completed,
        Cancelled
    }
}