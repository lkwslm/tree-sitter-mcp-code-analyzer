using System;
using System.Collections.Generic;
using System.Linq;

namespace ExampleProject.Services
{
    public interface IUserService
    {
        User GetUserById(int id);
        void CreateUser(User user);
        void UpdateUser(User user);
        void DeleteUser(int id);
        List<User> GetAllUsers();
    }

    public interface IOrderService
    {
        Order CreateOrder(int userId, decimal amount);
        void ProcessOrder(int orderId);
        List<Order> GetOrdersByUserId(int userId);
    }

    public class UserService : IUserService
    {
        private readonly IRepository<User> _userRepository;
        private readonly ILogger _logger;

        public UserService(IRepository<User> userRepository, ILogger logger)
        {
            _userRepository = userRepository ?? throw new ArgumentNullException(nameof(userRepository));
            _logger = logger ?? throw new ArgumentNullException(nameof(logger));
        }

        public User GetUserById(int id)
        {
            _logger.LogInfo($"Getting user with ID: {id}");
            return _userRepository.GetById(id);
        }

        public void CreateUser(User user)
        {
            if (user == null)
                throw new ArgumentNullException(nameof(user));

            _logger.LogInfo($"Creating user: {user.Name}");
            _userRepository.Add(user);
        }

        public void UpdateUser(User user)
        {
            if (user == null)
                throw new ArgumentNullException(nameof(user));

            _userRepository.Update(user);
        }

        public void DeleteUser(int id)
        {
            _userRepository.Delete(id);
        }

        public List<User> GetAllUsers()
        {
            return _userRepository.GetAll().ToList();
        }
    }
}