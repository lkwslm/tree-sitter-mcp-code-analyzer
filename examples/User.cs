using System;
using System.Collections.Generic;
using System.Linq;

namespace ExampleProject.Core
{
    /// <summary>
    /// 用户实体类
    /// </summary>
    public class User
    {
        private readonly int _id;
        private string _name;
        
        public int Id => _id;
        public string Name { get; set; }
        public string Email { get; set; }
        public DateTime CreatedAt { get; private set; }
        public List<Order> Orders { get; set; }

        public User(int id, string name)
        {
            _id = id;
            _name = name;
            CreatedAt = DateTime.Now;
            Orders = new List<Order>();
        }

        public void AddOrder(Order order)
        {
            if (order == null)
                throw new ArgumentNullException(nameof(order));
            
            Orders.Add(order);
        }

        public decimal GetTotalSpent()
        {
            return Orders.Sum(o => o.TotalAmount);
        }

        public virtual bool CanMakeOrder()
        {
            return true;
        }
    }

    public class PremiumUser : User
    {
        public double DiscountRate { get; set; }

        public PremiumUser(int id, string name, double discountRate) 
            : base(id, name)
        {
            DiscountRate = discountRate;
        }

        public override bool CanMakeOrder()
        {
            return GetTotalSpent() >= 0; // Premium users can always make orders
        }

        public decimal GetDiscountedTotal()
        {
            var total = GetTotalSpent();
            return total * (decimal)(1 - DiscountRate);
        }
    }
}